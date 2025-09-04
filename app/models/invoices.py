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
class InvoiceStatus(str, enum.Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"


# ----------------------
# INVOICES MODEL
# ----------------------
class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    sales_order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sales_orders.id"), nullable=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, server_default=func.now())
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status_enum"),
        default=InvoiceStatus.unpaid,
    ) 
    
    sales_person_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sales_persons.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="invoices")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="invoices")
    sales_person: Mapped["SalesPerson"] = relationship("SalesPerson", back_populates="invoices")
    invoice_items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="invoice")


# ----------------------
# INVOICE ITEMS MODEL
# ----------------------
class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False)
    so_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("so_items.id"), nullable=False)
    quantity_invoiced: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="invoice_items")
    so_item: Mapped["SOItem"] = relationship("SOItem", back_populates="invoice_items")


# ----------------------
# PAYMENTS MODEL
# ----------------------
class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False)
    payment_date: Mapped[Date] = mapped_column(Date, nullable=False)
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    reference: Mapped[str | None] = mapped_column(String, nullable=True)
    document: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")