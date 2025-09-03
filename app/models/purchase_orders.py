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
class PurchaseOrderStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    partial_received = "partial_received"
    received = "received"
    cancelled = "cancelled"


class POPaymentStatus(str, enum.Enum):
    unpaid = "unpaid"
    paid = "paid"


# ----------------------
# PURCHASE ORDERS MODEL
# ----------------------
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, server_default=func.now())
    expected_delivery_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="purchase_order_status_enum"),
        default=PurchaseOrderStatus.draft,
    )
    
    # Payment tracking
    payment_status: Mapped[POPaymentStatus] = mapped_column(
        Enum(POPaymentStatus, name="po_payment_status_enum"),
        default=POPaymentStatus.unpaid,
    )
    payment_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    payment_amount: Mapped[Numeric | None] = mapped_column(Numeric(10, 2), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String, nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    
    payment_terms: Mapped[str | None] = mapped_column(String, nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")
    items: Mapped[list["POItem"]] = relationship("POItem", back_populates="purchase_order")
    receipts: Mapped[list["PurchaseReceipt"]] = relationship("PurchaseReceipt", back_populates="purchase_order")


# ----------------------
# PO ITEMS MODEL
# ----------------------
class POItem(Base):
    __tablename__ = "po_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[Numeric] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="po_items")
    receipt_items: Mapped[list["ReceiptItem"]] = relationship("ReceiptItem", back_populates="po_item")


# ----------------------
# PURCHASE RECEIPTS MODEL
# ----------------------
class PurchaseReceipt(Base):
    __tablename__ = "purchase_receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    receipt_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    received_date: Mapped[Date] = mapped_column(Date, server_default=func.now())
    received_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="receipts")
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="receipts")
    received_by_user: Mapped["User"] = relationship("User", back_populates="received_receipts")
    receipt_items: Mapped[list["ReceiptItem"]] = relationship("ReceiptItem", back_populates="receipt")


# ----------------------
# RECEIPT ITEMS MODEL
# ----------------------
class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_receipts.id"), nullable=False)
    po_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("po_items.id"), nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    receipt: Mapped["PurchaseReceipt"] = relationship("PurchaseReceipt", back_populates="receipt_items")
    po_item: Mapped["POItem"] = relationship("POItem", back_populates="receipt_items")