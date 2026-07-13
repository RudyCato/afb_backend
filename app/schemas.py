from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict

from .models import OrderStatus, ShipmentStatus, InventoryReason, AssignmentStatus


# ---------- Customers ----------
class CustomerCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None


class CustomerOut(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Products ----------
class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    pack_size: Optional[str] = None
    unit_price: Optional[float] = None
    active: bool = True
    initial_qty: int = 0
    reorder_threshold: int = 10


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    category: str
    pack_size: Optional[str]
    unit_price: Optional[float]
    active: bool


# ---------- Inventory ----------
class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    sku: str
    name: str
    category: str
    location: str
    qty_on_hand: int
    qty_reserved: int
    qty_available: int
    reorder_threshold: int
    low_stock: bool
    last_updated: datetime


class InventoryAdjust(BaseModel):
    change_qty: int
    reason: InventoryReason = InventoryReason.adjustment
    reference: Optional[str] = None


# ---------- Orders ----------
class OrderItemCreate(BaseModel):
    product_id: int
    qty_ordered: int


class OrderCreate(BaseModel):
    customer: CustomerCreate
    items: List[OrderItemCreate]
    delivery_pref: Optional[str] = "Next available Tri-State delivery"
    notes: Optional[str] = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    sku: str
    name: str
    qty_ordered: int
    qty_packed: int


class OrderStatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: OrderStatus
    note: Optional[str]
    changed_at: datetime


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    status: OrderStatus
    delivery_pref: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    customer: CustomerOut
    items: List[OrderItemOut]
    status_history: List[OrderStatusHistoryOut]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: Optional[str] = None


# ---------- Packing ----------
class PackingCreate(BaseModel):
    packed_by: str
    boxes: int = 1
    notes: Optional[str] = None
    item_qty_packed: Optional[dict] = None   # {order_item_id: qty}


class PackingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    packed_by: str
    boxes: int
    notes: Optional[str]
    packed_at: datetime


# ---------- Shipping ----------
class ShipmentCreate(BaseModel):
    carrier: str
    tracking_number: Optional[str] = None
    address: Optional[str] = None


class ShipmentEventCreate(BaseModel):
    status: str
    location: Optional[str] = None
    notes: Optional[str] = None


class ShipmentEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    location: Optional[str]
    notes: Optional[str]
    created_at: datetime


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    carrier: str
    tracking_number: Optional[str]
    address: str
    status: ShipmentStatus
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    events: List[ShipmentEventOut]


# ---------- Packers & Production ----------
class PackerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    active: bool


class PackingAssignmentCreate(BaseModel):
    product_id: int
    qty_assigned: int
    assigned_to: str
    assigned_by: Optional[str] = None
    notes: Optional[str] = None


class PackingAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    sku: str
    product_name: str
    qty_assigned: int
    qty_completed: int
    assigned_to: str
    assigned_by: Optional[str]
    status: AssignmentStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class AssignmentStatusUpdate(BaseModel):
    status: AssignmentStatus


class ProductionLogCreate(BaseModel):
    packer_name: str
    product_id: int
    qty_completed: int
    assignment_id: Optional[int] = None
    notes: Optional[str] = None


class ProductionLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assignment_id: Optional[int]
    product_id: int
    sku: str
    product_name: str
    packer_name: str
    qty_completed: int
    notes: Optional[str]
    logged_at: datetime
