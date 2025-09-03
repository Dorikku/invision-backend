from sqlalchemy import String, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sku: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)

    cost_price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    selling_price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=True)
    image: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    so_items: Mapped[list["SOItem"]] = relationship("SOItem", back_populates="product")
    qo_items: Mapped[list["QOItem"]] = relationship("QOItem", back_populates="product")