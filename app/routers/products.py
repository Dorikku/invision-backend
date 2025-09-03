from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db import get_db
from app.models.products import Product as ProductModel
from app.schemas.schemas import ProductBase as ProductSchema

router = APIRouter(tags=["products"])

@router.get("/products", response_model=List[ProductSchema])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductModel).order_by(ProductModel.id))
    products = result.scalars().all()
    return [
        ProductSchema(
            id=product.id,
            name=product.name,
            sku=product.sku,
            description=product.description,
            category_id=product.category_id,
            quantity=product.quantity,
            # tax_rate=float(product.tax_rate),
            cost_price=float(product.cost_price),
            selling_price=float(product.selling_price),
            image=product.image
        )
        for product in products
    ]