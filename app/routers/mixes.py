from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/mixes", tags=["mixes"])


def _recipe_to_out(r: models.MixRecipe) -> schemas.MixRecipeOut:
    return schemas.MixRecipeOut(
        id=r.id, product_id=r.product_id, product_name=r.product.name,
        unit_weight_lb=r.unit_weight_lb, notes=r.notes,
        ingredients=[
            schemas.MixIngredientOut(
                ingredient_name=i.ingredient_name,
                ingredient_product_id=i.ingredient_product_id,
                percentage=i.percentage,
            )
            for i in r.ingredients
        ],
    )


@router.post("/recipes", response_model=schemas.MixRecipeOut)
def upsert_recipe(payload: schemas.MixRecipeCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    total_pct = sum(i.percentage for i in payload.ingredients)
    if payload.ingredients and abs(total_pct - 100.0) > 0.5:
        raise HTTPException(400, f"Ingredient percentages must add up to 100 (currently {total_pct}).")

    recipe = db.query(models.MixRecipe).filter(models.MixRecipe.product_id == payload.product_id).first()
    if not recipe:
        recipe = models.MixRecipe(product_id=payload.product_id)
        db.add(recipe)
        db.flush()
    else:
        db.query(models.MixIngredient).filter(models.MixIngredient.recipe_id == recipe.id).delete()

    recipe.unit_weight_lb = payload.unit_weight_lb
    recipe.notes = payload.notes

    for ing in payload.ingredients:
        db.add(models.MixIngredient(
            recipe_id=recipe.id, ingredient_name=ing.ingredient_name,
            ingredient_product_id=ing.ingredient_product_id, percentage=ing.percentage,
        ))

    db.commit()
    db.refresh(recipe)
    return _recipe_to_out(recipe)


@router.get("/recipes", response_model=list[schemas.MixRecipeOut])
def list_recipes(db: Session = Depends(get_db)):
    rows = db.query(models.MixRecipe).all()
    return [_recipe_to_out(r) for r in rows]


@router.get("/recipes/{product_id}", response_model=schemas.MixRecipeOut)
def get_recipe(product_id: int, db: Session = Depends(get_db)):
    recipe = db.query(models.MixRecipe).filter(models.MixRecipe.product_id == product_id).first()
    if not recipe:
        raise HTTPException(404, "No mix recipe for that product")
    return _recipe_to_out(recipe)


@router.get("/required-ingredients", response_model=schemas.MixRequirementOut)
def required_ingredients(product_id: int, qty: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    recipe = db.query(models.MixRecipe).filter(models.MixRecipe.product_id == product_id).first()
    if not recipe:
        raise HTTPException(404, "No mix recipe defined for that product yet")

    total_weight = round(recipe.unit_weight_lb * qty, 2)
    ingredients = [
        schemas.IngredientAmount(
            ingredient_name=i.ingredient_name,
            ingredient_product_id=i.ingredient_product_id,
            percentage=i.percentage,
            amount_lb=round(total_weight * i.percentage / 100, 2),
        )
        for i in recipe.ingredients
    ]

    return schemas.MixRequirementOut(
        product_id=product_id, product_name=product.name, qty_ordered=qty,
        unit_weight_lb=recipe.unit_weight_lb, total_weight_lb=total_weight,
        ingredients=ingredients,
    )
