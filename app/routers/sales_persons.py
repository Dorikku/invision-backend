from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db import get_db
from app.models.sales_persons import SalesPerson as SalesPersonModel
from app.schemas.schemas import SalesPerson as SalesPersonSchema


router = APIRouter(tags=["salespersons"])

@router.get("/salespersons", response_model=List[SalesPersonSchema])
async def list_sales_persons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SalesPersonModel).order_by(SalesPersonModel.id))
    sales_persons = result.scalars().all()
    return [
        SalesPersonSchema(
            id=sales_person.id,
            name=sales_person.name,
        )
        for sales_person in sales_persons
    ]