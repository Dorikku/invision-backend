from sqlalchemy import String, Integer, Text, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from . import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer_since: Mapped[Date] = mapped_column(
        Date, server_default=func.now()
    )

    # Relationships
    orders: Mapped[list["SalesOrder"]] = relationship("SalesOrder", back_populates="customer")
    quotations: Mapped[list["Quotation"]] = relationship("Quotation", back_populates="customer")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="customer")