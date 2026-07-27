from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict

from .models import (
    OrderStatus, ShipmentStatus, InventoryReason, AssignmentStatus, AssignmentPurpose,
    PalletStatus, ProductType, OrderTaskType, OrderTaskStatus, StaffRole, ReturnReason,
    ReceiptCondition,
)


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
    description: Optional[str] = None
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
    description: Optional[str] = None
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
    description: Optional[str] = None
    category: str
    location: str
    warehouse: Optional[str] = None
    aisle: Optional[str] = None
    bin_column: Optional[str] = None
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


class InventoryLocationUpdate(BaseModel):
    warehouse: Optional[str] = None
    aisle: Optional[str] = None
    bin_column: Optional[str] = None
    reorder_threshold: Optional[int] = None


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
    purpose: AssignmentPurpose = AssignmentPurpose.inventory
    order_number: Optional[str] = None
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
    purpose: AssignmentPurpose = AssignmentPurpose.inventory
    order_number: Optional[str] = None
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    materials_needed: List[MaterialLine] = []
    inventory_on_hand: int = 0


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


# ---------- Receipts ----------
class ReceiptCreate(BaseModel):
    product_id: int
    qty_received: int
    received_by: str
    qty_expected: Optional[int] = None
    vendor: Optional[str] = None
    po_number: Optional[str] = None
    lot_code: Optional[str] = None
    sell_by_date: Optional[date] = None
    condition: ReceiptCondition = ReceiptCondition.good
    temperature_f: Optional[float] = None
    put_away_warehouse: Optional[str] = None
    put_away_aisle: Optional[str] = None
    put_away_bin_column: Optional[str] = None
    notes: Optional[str] = None


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    sku: str
    product_name: str
    qty_received: int
    qty_expected: Optional[int]
    discrepancy: int = 0   # qty_expected - qty_received; 0 if no PO qty given
    vendor: Optional[str]
    po_number: Optional[str]
    lot_code: Optional[str]
    sell_by_date: Optional[date]
    condition: ReceiptCondition
    temperature_f: Optional[float]
    put_away_warehouse: Optional[str]
    put_away_aisle: Optional[str]
    put_away_bin_column: Optional[str]
    received_by: str
    notes: Optional[str]
    created_at: datetime


# ---------- Returns ----------
class ReturnCreate(BaseModel):
    product_id: int
    qty: int
    reason: ReturnReason
    order_number: Optional[str] = None
    customer_id: Optional[int] = None
    sell_by_date: Optional[date] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None


class ReturnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: Optional[str]
    customer_id: Optional[int]
    customer_name: Optional[str] = None
    product_id: int
    sku: str
    product_name: str
    qty: int
    sell_by_date: Optional[date]
    reason: ReturnReason
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime


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


# ---------- Order Tasks (picking, raw material packaging, labeling, boxing) ----------
class OrderTaskCreate(BaseModel):
    order_id: int
    task_type: OrderTaskType
    assigned_to: str
    assigned_by: Optional[str] = None
    notes: Optional[str] = None


class OrderTaskReassign(BaseModel):
    assigned_to: str


class OrderTaskOut(BaseModel):
    id: int
    order_id: int
    order_number: str
    task_type: OrderTaskType
    assigned_to: str
    assigned_by: Optional[str]
    status: OrderTaskStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_minutes: Optional[float]
    notes: Optional[str]
    created_at: datetime


class StaffBoardEntry(BaseModel):
    packer_name: str
    kind: str            # "order_task" | "bulk_assignment"
    label: str           # human-readable description of what they're doing
    status: str
    reference: str       # order number or product name, for click-through


# ---------- Product Mixer (recipes & ingredient scaling) ----------
class MixIngredientIn(BaseModel):
    ingredient_name: str
    ingredient_product_id: Optional[int] = None
    percentage: float


class MixRecipeCreate(BaseModel):
    product_id: int
    unit_weight_lb: float
    notes: Optional[str] = None
    ingredients: List[MixIngredientIn]


class MixIngredientOut(BaseModel):
    ingredient_name: str
    ingredient_product_id: Optional[int]
    percentage: float


class MixRecipeOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    unit_weight_lb: float
    notes: Optional[str]
    ingredients: List[MixIngredientOut]


class IngredientAmount(BaseModel):
    ingredient_name: str
    ingredient_product_id: Optional[int]
    percentage: float
    amount_lb: float


class MixRequirementOut(BaseModel):
    product_id: int
    product_name: str
    qty_ordered: int
    unit_weight_lb: float
    total_weight_lb: float
    ingredients: List[IngredientAmount]


# ---------- Staff auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class StaffMeOut(BaseModel):
    username: str
    full_name: str
    role: StaffRole
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ---------- Backups ----------
class BackupLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    destination: str
    status: str
    filename: Optional[str]
    size_bytes: Optional[int]
    triggered_by: Optional[str]
    error_message: Optional[str]
    created_at: datetime


class CloudBackupResult(BaseModel):
    ok: bool
    detail: str
    filename: Optional[str] = None
