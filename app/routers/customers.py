from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db import get_db
from app.models.customers import Customer as CustomerModel
from app.schemas.schemas import Customer as CustomerSchema

router = APIRouter(tags=["customers"])

@router.get("/customers", response_model=List[CustomerSchema])
async def list_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomerModel).order_by(CustomerModel.id))
    customers = result.scalars().all()
    return [
        CustomerSchema(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            address=customer.address,
            contact_person=customer.contact_person
        )
        for customer in customers
    ]