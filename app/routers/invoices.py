from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List
from datetime import datetime
from pydantic import BaseModel
from app.db import get_db
from app.models.invoices import Invoice as InvoiceModel, InvoiceItem as InvoiceItemModel, InvoiceStatus
from app.models.sales_orders import SalesOrder as SalesOrderModel, SOItem, SOInvoiceStatus
from app.schemas.schemas import LineItem, InvoiceSchema

router = APIRouter(tags=["invoices"])

class InvoiceItemCreate(BaseModel):
    soItemId: int
    quantity: int

class CreateInvoiceRequest(BaseModel):
    salesOrderId: int
    date: str
    dueDate: str
    notes: str | None = None
    items: List[InvoiceItemCreate]

class InvoicedQuantityResponse(BaseModel):
    soItemId: str
    quantity: int

async def generate_invoice_number(db: AsyncSession) -> str:
    """Generate sequential invoice number like INV-2025-001"""
    current_year = datetime.now().year
    
    result = await db.execute(
        select(InvoiceModel.invoice_number)
        .where(InvoiceModel.invoice_number.like(f"INV-{current_year}-%"))
        .order_by(InvoiceModel.invoice_number.desc())
        .limit(1)
    )
    last_invoice = result.scalar_one_or_none()
    
    if last_invoice:
        try:
            last_num = int(last_invoice.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    return f"INV-{current_year}-{new_num:03d}"

@router.get("/invoices", response_model=List[InvoiceSchema])
async def list_invoices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InvoiceModel)
        .options(
            selectinload(InvoiceModel.invoice_items)
            .selectinload(InvoiceItemModel.so_item)
            .selectinload(SOItem.product),
            selectinload(InvoiceModel.customer),
            selectinload(InvoiceModel.sales_person),
            selectinload(InvoiceModel.sales_order)
        )
        .order_by(InvoiceModel.created_at.desc())
    )
    invoices = result.scalars().unique().all()
    
    response = []
    for invoice in invoices:
        subtotal = 0.0
        tax = 0.0
        items = []
        for inv_item in invoice.invoice_items:
            so_item = inv_item.so_item
            item_total = float(inv_item.quantity_invoiced * so_item.price)
            item_tax = item_total * float(so_item.tax_rate)
            subtotal += item_total
            tax += item_tax

            items.append(
                LineItem(
                    id=str(inv_item.id),
                    productId=str(so_item.product_id),
                    productName=so_item.product.name if so_item.product else "Unknown",
                    description=so_item.product.description if so_item.product else None,
                    quantity=inv_item.quantity_invoiced,
                    unitCost=float(so_item.product.cost_price) if so_item.product else 0.0,
                    unitPrice=float(so_item.price),
                    total=item_total,
                    taxRate=float(so_item.tax_rate),
                    shippedQuantity=0
                )
            )

        total = subtotal + tax

        response.append(
            InvoiceSchema(
                id=invoice.id,
                invoiceNumber=invoice.invoice_number,
                salesOrderId=invoice.sales_order_id,
                customerId=invoice.customer_id,
                customerName=invoice.customer.name if invoice.customer else "Unknown",
                customerEmail=invoice.customer.email if invoice.customer else None,
                customerAddress=invoice.customer.address if invoice.customer else None,
                date=invoice.date.isoformat(),
                dueDate=invoice.due_date.isoformat(),
                subtotal=subtotal,
                tax=tax,
                total=total,
                status=invoice.status.value,
                notes=invoice.notes,
                createdAt=invoice.created_at.isoformat(),
                updatedAt=invoice.updated_at.isoformat(),
                items=items
            )
        )
    
    return response

@router.get("/sales-orders/{order_id}/invoiced-quantities", response_model=List[InvoicedQuantityResponse])
async def get_invoiced_quantities(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SalesOrderModel)
        .options(selectinload(SalesOrderModel.items))
        .where(SalesOrderModel.id == order_id)
    )
    sales_order = result.scalar_one_or_none()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")

    response = []
    for item in sales_order.items:
        result = await db.execute(
            select(func.sum(InvoiceItemModel.quantity_invoiced))
            .where(InvoiceItemModel.so_item_id == item.id)
        )
        invoiced_qty = result.scalar() or 0
        response.append(InvoicedQuantityResponse(soItemId=str(item.id), quantity=invoiced_qty))
    
    return response

@router.post("/invoices", response_model=InvoiceSchema)
async def create_invoice(
    request: CreateInvoiceRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        async with db.begin():
            result = await db.execute(
                select(SalesOrderModel)
                .options(selectinload(SalesOrderModel.items))
                .where(SalesOrderModel.id == request.salesOrderId)
            )
            sales_order = result.scalar_one_or_none()
            if not sales_order:
                raise HTTPException(status_code=404, detail="Sales order not found")

            invoice_number = await generate_invoice_number(db)

            invoice = InvoiceModel(
                invoice_number=invoice_number,
                sales_order_id=request.salesOrderId,
                customer_id=sales_order.customer_id,
                date=datetime.fromisoformat(request.date).date(),
                due_date=datetime.fromisoformat(request.dueDate).date(),
                status=InvoiceStatus.unpaid,
                sales_person_id=sales_order.sales_person_id,
                notes=request.notes
            )
            db.add(invoice)
            await db.flush()

            for item_data in request.items:
                result = await db.execute(
                    select(SOItem)
                    .where(SOItem.id == item_data.soItemId)
                )
                so_item = result.scalar_one_or_none()
                if not so_item or so_item.sales_order_id != sales_order.id:
                    raise HTTPException(status_code=400, detail=f"Invalid SO item ID: {item_data.soItemId}")

                result = await db.execute(
                    select(func.sum(InvoiceItemModel.quantity_invoiced))
                    .where(InvoiceItemModel.so_item_id == item_data.soItemId)
                )
                invoiced_qty = result.scalar() or 0
                if invoiced_qty + item_data.quantity > so_item.quantity:
                    raise HTTPException(status_code=400, detail=f"Quantity exceeds remaining for item {item_data.soItemId}")

                invoice_item = InvoiceItemModel(
                    invoice_id=invoice.id,
                    so_item_id=item_data.soItemId,
                    quantity_invoiced=item_data.quantity
                )
                db.add(invoice_item)

            fully_invoiced = True
            has_partial = False
            for so_item in sales_order.items:
                result = await db.execute(
                    select(func.sum(InvoiceItemModel.quantity_invoiced))
                    .where(InvoiceItemModel.so_item_id == so_item.id)
                )
                total_invoiced = result.scalar() or 0
                if total_invoiced < so_item.quantity:
                    fully_invoiced = False
                if total_invoiced > 0:
                    has_partial = True

            if fully_invoiced:
                sales_order.invoice_status = SOInvoiceStatus.invoiced
            elif has_partial:
                sales_order.invoice_status = SOInvoiceStatus.partial
            else:
                sales_order.invoice_status = SOInvoiceStatus.not_invoiced

        result = await db.execute(
            select(InvoiceModel)
            .options(
                selectinload(InvoiceModel.invoice_items)
                .selectinload(InvoiceItemModel.so_item)
                .selectinload(SOItem.product),
                selectinload(InvoiceModel.customer),
                selectinload(InvoiceModel.sales_person)
            )
            .where(InvoiceModel.id == invoice.id)
        )
        created_invoice = result.scalar_one()

        subtotal = 0.0
        tax = 0.0
        items = []
        for inv_item in created_invoice.invoice_items:
            so_item = inv_item.so_item
            item_total = float(inv_item.quantity_invoiced * so_item.price)
            item_tax = item_total * float(so_item.tax_rate)
            subtotal += item_total
            tax += item_tax

            items.append(
                LineItem(
                    id=str(inv_item.id),
                    productId=str(so_item.product_id),
                    productName=so_item.product.name if so_item.product else "Unknown",
                    description=so_item.product.description if so_item.product else None,
                    quantity=inv_item.quantity_invoiced,
                    unitCost=float(so_item.product.cost_price) if so_item.product else 0.0,
                    unitPrice=float(so_item.price),
                    total=item_total,
                    taxRate=float(so_item.tax_rate),
                    shippedQuantity=0
                )
            )

        total = subtotal + tax

        return InvoiceSchema(
            id=created_invoice.id,
            invoiceNumber=created_invoice.invoice_number,
            salesOrderId=created_invoice.sales_order_id,
            customerId=created_invoice.customer_id,
            customerName=created_invoice.customer.name if created_invoice.customer else "Unknown",
            customerEmail=created_invoice.customer.email if created_invoice.customer else None,
            customerAddress=created_invoice.customer.address if created_invoice.customer else None,
            date=created_invoice.date.isoformat(),
            dueDate=created_invoice.due_date.isoformat(),
            subtotal=subtotal,
            tax=tax,
            total=total,
            status=created_invoice.status.value,
            notes=created_invoice.notes,
            createdAt=created_invoice.created_at.isoformat(),
            updatedAt=created_invoice.updated_at.isoformat(),
            items=items
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create invoice: {str(e)}"
        )