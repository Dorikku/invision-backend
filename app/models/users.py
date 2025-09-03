from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from . import Base


# ----------------------
# ROLES MODEL
# ----------------------
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="role")


# ----------------------
# USERS MODEL
# ----------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    received_receipts: Mapped[list["PurchaseReceipt"]] = relationship("PurchaseReceipt", back_populates="received_by_user")