from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/products", tags=["products"])


class ProductPatch(BaseModel):
    """Partial update — only the fields the operator commonly edits from the
    inventory / stock UI. `None` on a field means 'do not change'; sending an
    empty string clears the field."""
    barcode: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[float] = None
    active: Optional[bool] = None


@router.post("", response_model=schemas.ProductOut)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Product).filter(models.Product.sku == payload.sku).first()
    if existing:
        raise HTTPException(400, "SKU already exists")
    data = payload.model_dump()
    initial_qty = data.pop("initial_qty")
    reorder_threshold = data.pop("reorder_threshold")
    product = models.Product(**data)
    db.add(product)
    db.commit()
    db.refresh(product)

    inv = models.Inventory(
        product_id=product.id, qty_on_hand=initial_qty, reorder_threshold=reorder_threshold
    )
    db.add(inv)
    if initial_qty:
        db.add(models.InventoryTransaction(
            product_id=product.id, change_qty=initial_qty,
            reason=models.InventoryReason.received_stock, reference="initial stock"
        ))
    db.commit()
    return product


@router.get("", response_model=list[schemas.ProductOut])
def list_products(category: str | None = None, item_type: models.ProductType | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Product)
    if category:
        q = q.filter(models.Product.category == category)
    if item_type:
        q = q.filter(models.Product.item_type == item_type)
    return q.order_by(models.Product.category, models.Product.name).all()


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.patch("/{product_id}", response_model=schemas.ProductOut)
def patch_product(product_id: int, payload: ProductPatch, db: Session = Depends(get_db)):
    """Partial update for the fields the ops UI edits from the stock page —
    barcode is the primary use case, but name/description/unit_price/active
    are here so we don't need a separate endpoint per field."""
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    data = payload.model_dump(exclude_unset=True)

    # If a barcode is being set, block a collision with a different product —
    # otherwise scan lookup would silently return the wrong product.
    if "barcode" in data and data["barcode"]:
        clash = (
            db.query(models.Product)
            .filter(models.Product.barcode == data["barcode"])
            .filter(models.Product.id != product_id)
            .first()
        )
        if clash:
            raise HTTPException(409, f"Barcode already assigned to SKU {clash.sku}.")

    for key, value in data.items():
        # Empty string on a text field clears it; treat "" as NULL for barcode.
        if key == "barcode" and value == "":
            value = None
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product
