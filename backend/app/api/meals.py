from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Meal, MealItem
from app.schemas.schemas import (
    MealCreate, MealUpdate, MealResponse, MealItemResponse,
    DailySummary,
)

router = APIRouter(prefix="/api/meals", tags=["meals"])


def _meal_to_response(meal: Meal) -> MealResponse:
    return MealResponse(
        id=meal.id,
        source_type=meal.source_type,
        notes=meal.notes,
        meal_label=meal.meal_label,
        image_path=meal.image_path,
        created_at=meal.created_at,
        items=[
            MealItemResponse(
                id=item.id,
                meal_id=item.meal_id,
                name=item.name,
                source=item.source,
                confidence=item.confidence,
                estimated_grams=item.estimated_grams,
                kcal=item.kcal,
                protein_g=item.protein_g,
                carbs_g=item.carbs_g,
                fat_g=item.fat_g,
                barcode=item.barcode,
                external_product_id=item.external_product_id,
            )
            for item in (meal.items or [])
        ],
    )


@router.get("/daily-summary", response_model=DailySummary)
def daily_summary(target_date: str = Query(alias="date"), db: Session = Depends(get_db)):
    try:
        dt = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(400, "Invalid date format, use YYYY-MM-DD")

    start = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
    end = datetime(dt.year, dt.month, dt.day, 23, 59, 59, tzinfo=timezone.utc)

    meals = db.query(Meal).filter(
        Meal.created_at >= start,
        Meal.created_at <= end,
    ).order_by(Meal.created_at.asc()).all()

    total_kcal = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    for m in meals:
        for item in (m.items or []):
            total_kcal += item.kcal or 0
            total_protein += item.protein_g or 0
            total_carbs += item.carbs_g or 0
            total_fat += item.fat_g or 0

    return DailySummary(
        date=target_date,
        total_kcal=round(total_kcal, 1),
        total_protein=round(total_protein, 1),
        total_carbs=round(total_carbs, 1),
        total_fat=round(total_fat, 1),
        meals=[_meal_to_response(m) for m in meals],
    )


@router.get("", response_model=list[MealResponse])
def list_meals(
    date_from: Optional[str] = Query(None, alias="date_from"),
    date_to: Optional[str] = Query(None, alias="date_to"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Meal).order_by(Meal.created_at.desc())
    if date_from:
        query = query.filter(Meal.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Meal.created_at <= datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59))
    meals = query.limit(limit).all()
    return [_meal_to_response(m) for m in meals]


@router.get("/{meal_id}", response_model=MealResponse)
def get_meal(meal_id: int, db: Session = Depends(get_db)):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(404, "Meal not found")
    return _meal_to_response(meal)


@router.post("", response_model=MealResponse, status_code=201)
def create_meal(payload: MealCreate, db: Session = Depends(get_db)):
    meal = Meal(
        source_type=payload.source_type,
        notes=payload.notes,
        meal_label=payload.meal_label,
        created_at=payload.created_at or datetime.now(timezone.utc),
    )
    db.add(meal)
    db.flush()

    for item_data in payload.items:
        item = MealItem(
            meal_id=meal.id,
            name=item_data.name,
            source=item_data.source,
            confidence=item_data.confidence,
            estimated_grams=item_data.estimated_grams,
            kcal=item_data.kcal,
            protein_g=item_data.protein_g,
            carbs_g=item_data.carbs_g,
            fat_g=item_data.fat_g,
            barcode=item_data.barcode,
            external_product_id=item_data.external_product_id,
        )
        db.add(item)

    db.commit()
    db.refresh(meal)
    return _meal_to_response(meal)


@router.put("/{meal_id}", response_model=MealResponse)
def update_meal(meal_id: int, payload: MealUpdate, db: Session = Depends(get_db)):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(404, "Meal not found")

    if payload.notes is not None:
        meal.notes = payload.notes

    if payload.items is not None:
        for old_item in meal.items:
            db.delete(old_item)
        for item_data in payload.items:
            item = MealItem(
                meal_id=meal.id,
                **item_data.model_dump(),
            )
            db.add(item)

    db.commit()
    db.refresh(meal)
    return _meal_to_response(meal)


@router.delete("/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(404, "Meal not found")
    db.delete(meal)
    db.commit()
    return {"ok": True}
