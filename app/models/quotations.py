from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    Numeric,
    Text,
    DateTime,
    Date,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from . import Base
import enum


# ----------------------
# ENUM DEFINITIONS
# ----------------------
class QuotationStatus(str, enum.Enum):
    open = "open"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


# ----------------------
# QUOTATIONS MODEL
# ----------------------
class Quotation(Base):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    quotation_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, server_default=func.now())
    
    status: Mapped[QuotationStatus] = mapped_column(
        Enum(QuotationStatus, name="quotation_status_enum"),
        default=QuotationStatus.open,
    )
    
    sales_person_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sales_persons.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    items: Mapped[list["QOItem"]] = relationship("QOItem", back_populates="quotation")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="quotations")
    sales_person: Mapped["SalesPerson"] = relationship("SalesPerson", back_populates="quotations")
    sales_orders: Mapped[list["SalesOrder"]] = relationship("SalesOrder", back_populates="quotation")


# ----------------------
# QO ITEMS MODEL
# ----------------------
class QOItem(Base):
    __tablename__ = "qo_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotations.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_rate: Mapped[Numeric] = mapped_column(Numeric(5, 4), nullable=False)  # e.g., 0.1200 for 12%
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="qo_items")