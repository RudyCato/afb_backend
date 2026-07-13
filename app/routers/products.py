from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/products", tags=["products"])


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
def list_products(category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Product)
    if category:
        q = q.filter(models.Product.category == category)
    return q.order_by(models.Product.category, models.Product.name).all()


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product
