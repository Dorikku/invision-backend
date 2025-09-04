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
class SOInvoiceStatus(str, enum.Enum):
    not_invoiced = "not_invoiced"
    partial = "partial"
    invoiced = "invoiced"


class PaymentStatus(str, enum.Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"


class ShipmentStatus(str, enum.Enum):
    not_shipped = "not_shipped"
    partial = "partial"
    shipped = "shipped"


# ----------------------
# SALES ORDERS MODEL
# ----------------------
class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    quotation_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("quotations.id"), nullable=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    sales_person_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sales_persons.id"), nullable=True)

    date: Mapped[Date] = mapped_column(Date, server_default=func.now())

    invoice_status: Mapped[SOInvoiceStatus] = mapped_column(
        Enum(SOInvoiceStatus, name="so_invoice_status_enum"),
        default=SOInvoiceStatus.not_invoiced,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="so_payment_status_enum"),
        default=PaymentStatus.unpaid,
    )
    shipment_status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus, name="so_shipment_status_enum"),
        default=ShipmentStatus.not_shipped,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    items: Mapped[list["SOItem"]] = relationship("SOItem", back_populates="sales_order", cascade="all, delete-orphan", passive_deletes=True)
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="sales_orders")
    shipments: Mapped[list["Shipment"]] = relationship("Shipment", back_populates="sales_order")
    sales_person: Mapped["SalesPerson"] = relationship("SalesPerson", back_populates="orders")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="sales_order", cascade="all, delete-orphan", passive_deletes=True)


# ----------------------
# SO ITEMS MODEL
# ----------------------
class SOItem(Base):
    __tablename__ = "so_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    sales_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_rate: Mapped[Numeric] = mapped_column(Numeric(5, 4), nullable=False)  # e.g., 0.1200 for 12%
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="so_items")
    invoice_items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="so_item")
    shipment_items: Mapped[list["ShipmentItem"]] = relationship("ShipmentItem", back_populates="so_item")