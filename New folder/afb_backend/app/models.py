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


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
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
    location = Column(String, default="Paterson, NJ - Main")
    qty_on_hand = Column(Integer, default=0)
    qty_reserved = Column(Integer, default=0)
    reorder_threshold = Column(Integer, default=10)
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
