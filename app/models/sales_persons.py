from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base


class SalesPerson(Base):
    __tablename__ = "sales_persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    orders: Mapped[list["SalesOrder"]] = relationship("SalesOrder", back_populates="sales_person")
    quotations: Mapped[list["Quotation"]] = relationship("Quotation", back_populates="sales_person")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="sales_person")