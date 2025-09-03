from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List
from datetime import datetime
from pydantic import BaseModel
from app.db import get_db
from app.models.sales_orders import SalesOrder as SalesOrderModel, SOItem
from app.schemas.schemas import LineItem, SalesOrder as SalesOrderSchema, CreateSalesOrderRequest
from app.models.customers import Customer
from app.models.products import Product
from app.models.shipments import Shipment
from app.models.sales_persons import SalesPerson
from app.models.quotations import Quotation
from app.models.invoices import Invoice
from app.models.categories import Category



router = APIRouter(tags=["sales-orders"])


async def generate_order_number(db: AsyncSession) -> str:
    """Generate sequential order number like SO-2025-001"""
    current_year = datetime.now().year
    
    # Find the highest order number for current year
    result = await db.execute(
        select(SalesOrderModel.order_number)
        .where(SalesOrderModel.order_number.like(f"SO-{current_year}-%"))
        .order_by(SalesOrderModel.order_number.desc())
        .limit(1)
    )
    last_order = result.scalar_one_or_none()
    
    if last_order:
        # Extract number and increment (e.g., "SO-2025-001" -> 2)
        try:
            last_num = int(last_order.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    return f"SO-{current_year}-{new_num:03d}"  # Zero-padded 3 digits


@router.post("/sales-orders", response_model=SalesOrderSchema)
async def create_sales_order(
    request: CreateSalesOrderRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        async with db.begin():
            order_number = await generate_order_number(db)

            sales_order = SalesOrderModel(
                order_number=order_number,
                customer_id=request.customer_id,
                sales_person_id=request.sales_person_id,
                date=datetime.fromisoformat(request.date).date(),
                invoice_status=request.invoice_status,
                payment_status=request.payment_status,
                shipment_status=request.shipment_status,
                notes=request.notes
            )
            db.add(sales_order)
            await db.flush()

            for item_data in request.items:
                so_item = SOItem(
                    sales_order_id=sales_order.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                    price=item_data.price,
                    tax_rate=item_data.tax_rate
                )
                db.add(so_item)

        # 🔑 re-query with eager load to get relationships
        result = await db.execute(
            select(SalesOrderModel)
            .options(
                selectinload(SalesOrderModel.customer),
                selectinload(SalesOrderModel.sales_person),
                selectinload(SalesOrderModel.items).selectinload(SOItem.product)
            )
            .where(SalesOrderModel.id == sales_order.id)
        )
        created_order = result.scalar_one()

        # Build response
        subtotal, tax, items = 0.0, 0.0, []
        for item in created_order.items:
            item_total = float(item.quantity * item.price)
            item_tax = item_total * float(item.tax_rate)
            subtotal += item_total
            tax += item_tax

            items.append(
                LineItem(
                    id=str(item.id),
                    productId=str(item.product_id),
                    productName=item.product.name if item.product else "Unknown",
                    description=item.product.description if item.product else None,
                    quantity=item.quantity,
                    unitCost=float(item.product.cost_price) if item.product else 0.0,
                    unitPrice=float(item.price),
                    total=item_total,
                    taxRate=float(item.tax_rate),
                    shippedQuantity=0,
                )
            )

        total = subtotal + tax

        return SalesOrderSchema(
            id=created_order.id,
            orderNumber=created_order.order_number,
            quotationId=created_order.quotation_id,
            customerId=created_order.customer_id,
            customerName=created_order.customer.name if created_order.customer else "Unknown",
            customerContactPerson=created_order.customer.contact_person if created_order.customer else None,
            customerEmail=created_order.customer.email if created_order.customer else None,
            customerAddress=created_order.customer.address if created_order.customer else None,
            salesPersonId=created_order.sales_person_id,
            salesPersonName=created_order.sales_person.name if created_order.sales_person else None,
            date=created_order.date.isoformat(),
            deliveryDate=None,
            subtotal=subtotal,
            tax=tax,
            total=total,
            invoiceStatus=created_order.invoice_status.value,
            paymentStatus=created_order.payment_status.value,
            shipmentStatus=created_order.shipment_status.value,
            notes=created_order.notes,
            createdAt=created_order.created_at.isoformat(),
            updatedAt=created_order.updated_at.isoformat(),
            items=items,
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create sales order: {str(e)}"
        )




@router.get("/sales-orders", response_model=List[SalesOrderSchema])
async def list_sales_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SalesOrderModel)
        .options(
            selectinload(SalesOrderModel.items).selectinload(SOItem.product),
            selectinload(SalesOrderModel.customer),
            selectinload(SalesOrderModel.shipments).selectinload(Shipment.shipment_items),
            selectinload(SalesOrderModel.sales_person),
            selectinload(SalesOrderModel.quotation)
        )
        .order_by(SalesOrderModel.created_at.desc())
    )
    orders = result.scalars().unique().all()
    
    # Transform the data to match the desired response format
    response = []
    for order in orders:
        # Calculate totals from line items
        subtotal = 0.0
        tax = 0.0
        
        for item in order.items:
            item_total = float(item.quantity * item.price)
            item_tax = item_total * float(item.tax_rate)
            subtotal += item_total
            tax += item_tax
        
        total = subtotal + tax
        tax_rate = tax / subtotal if subtotal > 0 else 0.0
        
        # Get delivery date from the first shipment if available
        delivery_date = None
        if order.shipments:
            delivery_date = order.shipments[0].date_delivered
        
        # Prepare line items
        items = []
        for item in order.items:
            # Calculate shipped quantity from shipment_items
            shipped_quantity = 0
            for shipment in order.shipments:
                for shipment_item in shipment.shipment_items:
                    if shipment_item.so_item_id == item.id:
                        shipped_quantity += shipment_item.quantity_shipped
            
            item_total = float(item.quantity * item.price)
            item_tax = item_total * float(item.tax_rate)
            
            items.append(
                LineItem(
                    id=str(item.id),  # Keep as string for line items
                    productId=str(item.product_id),
                    productName=item.product.name if item.product else "Unknown",
                    description=item.product.description if item.product else None,
                    quantity=item.quantity,
                    unitCost=float(item.product.cost_price) if item.product else 0.0,
                    unitPrice=float(item.price),
                    total=item_total,
                    taxRate=float(item.tax_rate),
                    shippedQuantity=shipped_quantity
                )
            )
        
        response.append(
            SalesOrderSchema(
                id=order.id,  # Keep as integer
                orderNumber=order.order_number,
                quotationId=order.quotation_id,
                customerId=order.customer_id,
                customerName=order.customer.name if order.customer else "Unknown",
                customerContactPerson=order.customer.contact_person if order.customer else None,
                customerEmail=order.customer.email if order.customer else None,
                customerAddress=order.customer.address if order.customer else None,
                salesPersonId=order.sales_person.id,
                salesPersonName=order.sales_person.name if order.sales_person else None,
                date=order.date.isoformat(),
                deliveryDate=delivery_date.isoformat() if delivery_date else None,
                subtotal=subtotal,
                tax=tax,
                total=total,
                invoiceStatus=order.invoice_status.value,
                paymentStatus=order.payment_status.value,
                shipmentStatus=order.shipment_status.value,
                notes=order.notes,
                createdAt=order.created_at.isoformat(),
                updatedAt=order.updated_at.isoformat(),
                items=items
            )
        )
    
    return response


@router.get("/sales-orders/{order_id}", response_model=SalesOrderSchema)
async def get_sales_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SalesOrderModel)
        .options(
            selectinload(SalesOrderModel.items).selectinload(SOItem.product),
            selectinload(SalesOrderModel.customer),
            selectinload(SalesOrderModel.shipments),
            selectinload(SalesOrderModel.sales_person)
        )
        .where(SalesOrderModel.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Calculate totals from line items (same logic as list endpoint)
    subtotal = 0.0
    tax = 0.0
    
    for item in order.items:
        item_total = float(item.quantity * item.price)
        item_tax = item_total * float(item.tax_rate)
        subtotal += item_total
        tax += item_tax
    
    total = subtotal + tax
    tax_rate = tax / subtotal if subtotal > 0 else 0.0
    
    # Get delivery date from the first shipment if available
    delivery_date = None
    if order.shipments:
        delivery_date = order.shipments[0].date_delivered
    
    # Prepare line items
    items = []
    for item in order.items:
        # Calculate shipped quantity from shipment_items
        shipped_quantity = 0
        for shipment in order.shipments:
            for shipment_item in shipment.shipment_items:
                if shipment_item.so_item_id == item.id:
                    shipped_quantity += shipment_item.quantity_shipped
        
        item_total = float(item.quantity * item.price)
        item_tax = item_total * float(item.tax_rate)
        
        items.append(
            LineItem(
                id=str(item.id),
                productId=str(item.product_id),
                productName=item.product.name if item.product else "Unknown",
                description=item.product.description if item.product else None,
                quantity=item.quantity,
                unitCost=float(item.product.cost_price) if item.product else 0.0,
                unitPrice=float(item.price),
                total=item_total,
                taxRate=float(item.tax_rate),
                shippedQuantity=shipped_quantity
            )
        )

    return SalesOrderSchema(
        id=order.id,  # Keep as integer
        orderNumber=order.order_number,
        quotationId=order.quotation_id,
        customerId=order.customer_id,
        customerName=order.customer.name,
        customerContactPerson=order.customer.contact_person if order.customer else None,
        customerEmail=order.customer.email if order.customer else None,
        customerAddress=order.customer.address if order.customer else None,
        salesPersonId=order.sales_person.id,            
        salesPersonName=order.sales_person.name,
        date=order.date.isoformat(),
        deliveryDate=delivery_date.isoformat() if delivery_date else None,
        subtotal=subtotal,
        tax=tax,
        total=total,
        invoiceStatus=order.invoice_status.value,
        paymentStatus=order.payment_status.value,
        shipmentStatus=order.shipment_status.value,
        notes=order.notes,
        createdAt=order.created_at.isoformat(),
        updatedAt=order.updated_at.isoformat(),
        items=items
    )