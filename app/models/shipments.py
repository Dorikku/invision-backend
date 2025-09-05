from sqlalchemy import String, Integer, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from . import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    sales_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    carrier: Mapped[str] = mapped_column(String, nullable=True)
    date_delivered: Mapped[Date | None] = mapped_column(Date, nullable=True)
    tracker: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="shipments")
    shipment_items: Mapped[list["ShipmentItem"]] = relationship("ShipmentItem", back_populates="shipment")


class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("shipments.id"), nullable=False)
    so_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("so_items.id"), nullable=False)
    quantity_shipped: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="shipment_items")
    so_item: Mapped["SOItem"] = relationship("SOItem", back_populates="shipment_items")