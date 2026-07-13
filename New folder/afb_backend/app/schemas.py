from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict

from .models import OrderStatus, ShipmentStatus, InventoryReason, AssignmentStatus, PalletStatus, ProductType


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
    item_type: ProductType = ProductType.sellable
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
    item_type: ProductType
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


class PackingRecordBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    packed_by: str
    boxes: int
    packed_at: datetime


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
    packing_records: List[PackingRecordBrief] = []
    pallet_number: Optional[str] = None


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


class MaterialLine(BaseModel):
    role: str          # "container" | "lid" | "box"
    product_id: int
    sku: str
    name: str
    qty_needed: int


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
    materials_needed: List[MaterialLine] = []


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


# ---------- Pallets & Manifests ----------
class PalletCreate(BaseModel):
    loaded_by: str
    carrier: Optional[str] = None
    notes: Optional[str] = None


class PalletOrderBrief(BaseModel):
    order_number: str
    customer_name: str
    company: Optional[str]
    item_count: int
    status: OrderStatus


class PalletOut(BaseModel):
    id: int
    pallet_number: str
    loaded_by: str
    carrier: Optional[str]
    status: PalletStatus
    notes: Optional[str]
    created_at: datetime
    shipped_at: Optional[datetime]
    order_count: int


class PalletManifestItem(BaseModel):
    sku: str
    name: str
    qty: int


class PalletManifestOrder(BaseModel):
    order_number: str
    customer_name: str
    company: Optional[str]
    address: Optional[str]
    items: List[PalletManifestItem]


class PalletManifestOut(BaseModel):
    pallet_number: str
    loaded_by: str
    carrier: Optional[str]
    status: PalletStatus
    created_at: datetime
    shipped_at: Optional[datetime]
    orders: List[PalletManifestOrder]


class PalletAssignOrder(BaseModel):
    order_number: str


class PalletStatusUpdate(BaseModel):
    status: PalletStatus


# ---------- Packaging Specs & Materials ----------
class PackagingSpecCreate(BaseModel):
    product_id: int
    container_product_id: Optional[int] = None
    container_qty_per_unit: int = 1
    lid_product_id: Optional[int] = None
    lid_qty_per_unit: int = 1
    box_product_id: Optional[int] = None
    units_per_box: int = 1
    notes: Optional[str] = None


class PackagingSpecOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    container_product_id: Optional[int]
    container_name: Optional[str]
    container_qty_per_unit: int
    lid_product_id: Optional[int]
    lid_name: Optional[str]
    lid_qty_per_unit: int
    box_product_id: Optional[int]
    box_name: Optional[str]
    units_per_box: int
    notes: Optional[str]


class MaterialsNeededOut(BaseModel):
    product_id: int
    qty_ordered: int
    has_spec: bool
    materials: List[MaterialLine]
