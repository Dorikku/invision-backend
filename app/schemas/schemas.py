from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime
from enum import Enum

# Status Enums for better validation
class SOInvoiceStatus(str, Enum):
    not_invoiced = "not_invoiced"
    partial = "partial"
    invoiced = "invoiced"

class PaymentStatus(str, Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"

class ShipmentStatus(str, Enum):
    not_shipped = "not_shipped"
    partial = "partial"
    shipped = "shipped"

class InvoiceStatus(str, Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"

# Line Item schemas
class LineItemCreate(BaseModel):
    productId: int
    productName: str
    description: Optional[str] = None
    quantity: int
    unitCost: float
    unitPrice: float
    total: float
    # taxAmount: float
    taxRate: float
    shippedQuantity: int = 0

class LineItem(LineItemCreate):
    id: int

    class Config:
        from_attributes = True

# Sales Order schemas
# class SalesOrderCreate(BaseModel):
#     quotationId: Optional[int] = None
#     customerId: int
#     customerName: str
#     customerEmail: Optional[str] = None
#     customerAddress: Optional[str] = None
#     # salesPersonId: int = None
#     date: date
#     deliveryDate: Optional[date] = None
#     subtotal: float
#     tax: float
#     # taxRate: float = 0.0
#     total: float
#     invoiceStatus: InvoiceStatus = InvoiceStatus.not_invoiced
#     paymentStatus: PaymentStatus = PaymentStatus.unpaid
#     shipmentStatus: ShipmentStatus = ShipmentStatus.not_shipped
#     notes: Optional[str] = None
#     items: List[LineItemCreate]

# Request schemas for creating sales orders
class CreateSOItemRequest(BaseModel):
    product_id: int
    quantity: int
    price: float
    tax_rate: float

class CreateSalesOrderRequest(BaseModel):
    customer_id: int
    sales_person_id: int
    date: str
    invoice_status: SOInvoiceStatus = SOInvoiceStatus.not_invoiced
    payment_status: PaymentStatus = PaymentStatus.unpaid
    shipment_status: ShipmentStatus = ShipmentStatus.not_shipped
    notes: str = ""
    items: List[CreateSOItemRequest]

class SalesOrder(BaseModel):
    id: int
    orderNumber: str
    quotationId: Optional[int]
    customerId: int
    customerName: str
    customerContactPerson: Optional[str]
    customerEmail: Optional[EmailStr]
    customerAddress: Optional[str]
    salesPersonId: int
    salesPersonName: str
    date: date
    deliveryDate: Optional[date]
    subtotal: float
    tax: float
    # taxRate: float
    total: float
    invoiceStatus: str
    paymentStatus: str
    shipmentStatus: str
    notes: Optional[str]
    createdAt: datetime
    updatedAt: datetime
    items: List[LineItem]

    class Config:
        from_attributes = True

class Customer(BaseModel):
    id: int  
    name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    customer_since: Optional[datetime] = None

    class Config:
        from_attributes = True

class SalesPerson(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    id: int 
    name: str
    sku: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    quantity: int
    # tax_rate: float
    cost_price: float
    selling_price: float
    image: Optional[str] = None

    class Config:
        from_attributes = True
        # extra = "allow"  # Allow extra fields like 'price' for compatibility

class ShipmentBase(BaseModel):
    id: int
    sales_order_id: int
    carrier: str
    date_delivered: Optional[date]
    tracker: Optional[str]

    class Config:
        from_attributes = True

class SalesPersonBase(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


# Invoice Schema
class InvoiceSchema(BaseModel):
    id: int
    invoiceNumber: str
    salesOrderId: Optional[int]
    customerId: int
    customerName: str
    customerEmail: Optional[str]
    customerAddress: Optional[str]
    date: str  # ISO format date (e.g., "2025-09-05")
    dueDate: str  # ISO format date (e.g., "2025-10-05")
    subtotal: float
    tax: float
    total: float
    status: InvoiceStatus
    notes: Optional[str]
    createdAt: str  # ISO format datetime (e.g., "2025-09-05T01:02:00Z")
    updatedAt: str  # ISO format datetime (e.g., "2025-09-05T01:02:00Z")
    items: List[LineItem]

    class Config:
        from_attributes = True  # Enables ORM compatibility

# InvoiceItem Create Schema (used in CreateInvoiceRequest)
class InvoiceItemCreate(BaseModel):
    soItemId: int
    quantity: int

# Create Invoice Request Schema
class CreateInvoiceRequest(BaseModel):
    salesOrderId: int
    date: str  # ISO format date
    dueDate: str  # ISO format date
    notes: Optional[str]
    items: List[InvoiceItemCreate]