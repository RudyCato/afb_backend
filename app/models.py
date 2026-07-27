import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship

from .database import Base


class OrderStatus(str, enum.Enum):
    received = "received"
    confirmed = "confirmed"
    on_hold = "on_hold"
    picking = "picking"
    packing = "packing"
    packed = "packed"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class ShipmentStatus(str, enum.Enum):
    pending = "pending"
    in_transit = "in_transit"
    delivered = "delivered"
    exception = "exception"


class InventoryReason(str, enum.Enum):
    received_stock = "received_stock"
    order_reserved = "order_reserved"
    order_released = "order_released"
    order_shipped = "order_shipped"
    adjustment = "adjustment"
    production_completed = "production_completed"
    removed = "removed"          # damaged, lost, samples taken, etc. — leaves the building
    returned = "returned"        # customer return, unused pull, etc. — comes back into stock


class AssignmentStatus(str, enum.Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class PalletStatus(str, enum.Enum):
    building = "building"     # being loaded
    staged = "staged"         # full, waiting for pickup
    shipped = "shipped"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")


class ProductType(str, enum.Enum):
    sellable = "sellable"
    indirect_material = "indirect_material"
    raw_material = "raw_material"


class OrderTaskType(str, enum.Enum):
    picking = "picking"                                 # warehouse manager: pull raw bulk + packaging materials
    raw_material_packaging = "raw_material_packaging"    # packer: fill containers from bulk
    labeling = "labeling"                                # packer: apply labels
    boxing = "boxing"                                    # packer: box for shipment


class OrderTaskStatus(str, enum.Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"


class OrderTask(Base):
    """
    One granular, timed step in fulfilling a specific order — picking, then
    raw material packaging, labeling, and boxing. Each step is independently
    assignable/reassignable to a packer or helper, and timed for end-of-day
    production reporting.
    """
    __tablename__ = "order_tasks"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    task_type = Column(Enum(OrderTaskType), nullable=False)
    assigned_to = Column(String, nullable=False)
    assigned_by = Column(String, nullable=True)
    status = Column(Enum(OrderTaskStatus), default=OrderTaskStatus.assigned)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order")


class MixRecipe(Base):
    """
    Defines the ingredient composition of a mix/blended product (e.g. a
    granola or trail mix), so required ingredient amounts can be computed
    from an order quantity (e.g. 1 case of Crispy Granola -> 33 lbs -> broken
    down into lbs of each ingredient).
    """
    __tablename__ = "mix_recipes"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    unit_weight_lb = Column(Float, nullable=False)   # total weight per sellable unit (e.g. per case)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", foreign_keys=[product_id])
    ingredients = relationship("MixIngredient", back_populates="recipe", cascade="all, delete-orphan")


class MixIngredient(Base):
    __tablename__ = "mix_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("mix_recipes.id"), nullable=False)
    ingredient_name = Column(String, nullable=False)
    ingredient_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # optional link to tracked raw material stock
    percentage = Column(Float, nullable=False)   # % of total mix weight

    recipe = relationship("MixRecipe", back_populates="ingredients")
    ingredient_product = relationship("Product", foreign_keys=[ingredient_product_id])


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)   # longer item description, separate from the short catalog name
    category = Column(String, nullable=False)
    pack_size = Column(String, nullable=True)   # e.g. "25 lb case"
    unit_price = Column(Float, nullable=True)   # optional, fill in later
    barcode = Column(String, nullable=True, unique=False, index=True)  # placeholder for future barcode scanning
    item_type = Column(Enum(ProductType), default=ProductType.sellable, nullable=False)
    active = Column(Boolean, default=True)

    inventory = relationship("Inventory", back_populates="product", uselist=False)
    order_items = relationship("OrderItem", back_populates="product")
    packaging_spec = relationship(
        "PackagingSpec", back_populates="product", uselist=False,
        foreign_keys="PackagingSpec.product_id",
    )


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    location = Column(String, default="Paterson, NJ - Main")   # kept for display/back-compat
    warehouse = Column(String, nullable=True, default="Main")
    aisle = Column(String, nullable=True)
    bin_column = Column(String, nullable=True)   # the "column" in a warehouse's aisle/column/shelf scheme
    qty_on_hand = Column(Integer, default=0)
    qty_reserved = Column(Integer, default=0)
    reorder_threshold = Column(Integer, default=10)   # "min qty" — reorder point
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="inventory")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    change_qty = Column(Integer, nullable=False)   # positive or negative
    reason = Column(Enum(InventoryReason), nullable=False)
    reference = Column(String, nullable=True)      # e.g. order_number
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.received)
    delivery_pref = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    pallet_id = Column(Integer, ForeignKey("pallets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    packing_records = relationship("PackingRecord", back_populates="order", cascade="all, delete-orphan")
    shipment = relationship("Shipment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    pallet = relationship("Pallet", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    qty_ordered = Column(Integer, nullable=False)
    qty_packed = Column(Integer, default=0)
    unit_price_snapshot = Column(Float, nullable=True)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    note = Column(String, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="status_history")


class PackingRecord(Base):
    __tablename__ = "packing_records"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    packed_by = Column(String, nullable=False)
    boxes = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    packed_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="packing_records")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    carrier = Column(String, nullable=False)   # e.g. "AFB Fleet", "Private Trucking Partner"
    tracking_number = Column(String, nullable=True)
    address = Column(Text, nullable=False)
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.pending)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="shipment")
    events = relationship("ShipmentEvent", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentEvent(Base):
    __tablename__ = "shipment_events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    status = Column(String, nullable=False)
    location = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    shipment = relationship("Shipment", back_populates="events")


class Packer(Base):
    __tablename__ = "packers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PackingAssignment(Base):
    __tablename__ = "packing_assignments"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    qty_assigned = Column(Integer, nullable=False)
    qty_completed = Column(Integer, default=0)
    assigned_to = Column(String, nullable=False)   # packer name
    assigned_by = Column(String, nullable=True)     # packing manager name
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.assigned)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product")
    production_logs = relationship("PackerProductionLog", back_populates="assignment")


class PackerProductionLog(Base):
    __tablename__ = "packer_production_logs"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("packing_assignments.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    packer_name = Column(String, nullable=False)
    qty_completed = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("PackingAssignment", back_populates="production_logs")
    product = relationship("Product")


class Pallet(Base):
    __tablename__ = "pallets"

    id = Column(Integer, primary_key=True, index=True)
    pallet_number = Column(String, unique=True, index=True, nullable=False)  # e.g. "PLT-000123" — barcode-ready
    loaded_by = Column(String, nullable=False)      # who placed packages on the pallet
    carrier = Column(String, nullable=True)
    status = Column(Enum(PalletStatus), default=PalletStatus.building)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    shipped_at = Column(DateTime, nullable=True)

    orders = relationship("Order", back_populates="pallet")


class StaffRole(str, enum.Enum):
    admin = "admin"           # full access — owner/consultant
    manager = "manager"       # dashboard + applications admin
    packer = "packer"         # production page only


class StaffUser(Base):
    __tablename__ = "staff_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(StaffRole), default=StaffRole.packer, nullable=False)
    active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)


class BackupDestination(str, enum.Enum):
    local = "local"     # downloaded to whoever clicked the button's own machine
    cloud = "cloud"     # pushed to configured S3-compatible storage


class BackupStatus(str, enum.Enum):
    success = "success"
    failed = "failed"


class BackupLog(Base):
    __tablename__ = "backup_logs"

    id = Column(Integer, primary_key=True, index=True)
    destination = Column(Enum(BackupDestination), nullable=False)
    status = Column(Enum(BackupStatus), nullable=False)
    filename = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    triggered_by = Column(String, nullable=True)   # staff username
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PackagingSpec(Base):
    """
    Defines what indirect materials (container, lid, box) a sellable product
    needs, and how many sellable units fit per box — lets the system compute
    exactly how many containers/lids/boxes a packing job requires.
    """
    __tablename__ = "packaging_specs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)

    container_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    container_qty_per_unit = Column(Integer, default=1)   # containers needed per sellable unit

    lid_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    lid_qty_per_unit = Column(Integer, default=1)          # lids needed per sellable unit (separate item)

    box_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    units_per_box = Column(Integer, default=1)             # how many sellable units fit in one box

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="packaging_spec", foreign_keys=[product_id])
    container_product = relationship("Product", foreign_keys=[container_product_id])
    lid_product = relationship("Product", foreign_keys=[lid_product_id])
    box_product = relationship("Product", foreign_keys=[box_product_id])
