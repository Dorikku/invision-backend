from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import List
from datetime import datetime
from pydantic import BaseModel
from app.db import get_db
from app.models.sales_orders import SalesOrder as SalesOrderModel, SOItem, ShipmentStatus
from app.models.shipments import Shipment as ShipmentModel, ShipmentItem as ShipmentItemModel

router = APIRouter(tags=["shipments"])

class ShipmentItemCreate(BaseModel):
    soItemId: int
    quantity: int

class CreateShipmentRequest(BaseModel):
    salesOrderId: int
    date: str
    carrier: str
    tracker: str | None = None
    items: List[ShipmentItemCreate]

class ShippedQuantityResponse(BaseModel):
    soItemId: str
    quantity: int

@router.get("/sales-orders/{order_id}/shipped-quantities", response_model=List[ShippedQuantityResponse])
async def get_shipped_quantities(order_id: int, db: AsyncSession = Depends(get_db)):
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
            select(func.sum(ShipmentItemModel.quantity_shipped))
            .where(ShipmentItemModel.so_item_id == item.id)
        )
        shipped_qty = result.scalar() or 0
        response.append(ShippedQuantityResponse(soItemId=str(item.id), quantity=shipped_qty))
    
    return response

@router.post("/shipments", status_code=status.HTTP_201_CREATED)
async def create_shipment(
    request: CreateShipmentRequest,
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

            shipment = ShipmentModel(
                sales_order_id=request.salesOrderId,
                carrier=request.carrier,
                date_delivered=datetime.fromisoformat(request.date).date() if request.date else None,
                tracker=request.tracker
            )
            db.add(shipment)
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
                    select(func.sum(ShipmentItemModel.quantity_shipped))
                    .where(ShipmentItemModel.so_item_id == item_data.soItemId)
                )
                shipped_qty = result.scalar() or 0
                if shipped_qty + item_data.quantity > so_item.quantity:
                    raise HTTPException(status_code=400, detail=f"Quantity exceeds remaining for item {item_data.soItemId}")

                shipment_item = ShipmentItemModel(
                    shipment_id=shipment.id,
                    so_item_id=item_data.soItemId,
                    quantity_shipped=item_data.quantity
                )
                db.add(shipment_item)

            fully_shipped = True
            has_partial = False
            for so_item in sales_order.items:
                result = await db.execute(
                    select(func.sum(ShipmentItemModel.quantity_shipped))
                    .where(ShipmentItemModel.so_item_id == so_item.id)
                )
                total_shipped = result.scalar() or 0
                if total_shipped < so_item.quantity:
                    fully_shipped = False
                if total_shipped > 0:
                    has_partial = True

            if fully_shipped:
                sales_order.shipment_status = ShipmentStatus.shipped
            elif has_partial:
                sales_order.shipment_status = ShipmentStatus.partial
            else:
                sales_order.shipment_status = ShipmentStatus.not_shipped

        return {"message": "Shipment created successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create shipment: {str(e)}"
        )