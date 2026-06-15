"""
Seed the database with sample meals for testing.
Run: python -m app.seed_data
"""
from datetime import datetime, timezone, timedelta

from app.db.database import SessionLocal, init_db
from app.db.models import Meal, MealItem


def seed():
    init_db()
    db = SessionLocal()

    if db.query(Meal).count() > 0:
        print("Database already has data, skipping seed.")
        db.close()
        return

    now = datetime.now(timezone.utc)

    meal1 = Meal(
        created_at=now - timedelta(hours=3),
        source_type="photo",
        notes="Pranzo di oggi",
    )
    meal2 = Meal(
        created_at=now - timedelta(hours=8),
        source_type="manual",
        notes="Colazione",
    )

    db.add(meal1)
    db.add(meal2)
    db.flush()

    items1 = [
        MealItem(
            meal_id=meal1.id,
            name="Pasta al pomodoro",
            source="classification",
            confidence=0.89,
            estimated_grams=200,
            kcal=262,
            protein_g=10,
            carbs_g=50,
            fat_g=2.2,
        ),
        MealItem(
            meal_id=meal1.id,
            name="Pollo arrosto",
            source="classification",
            confidence=0.76,
            estimated_grams=150,
            kcal=247.5,
            protein_g=46.5,
            carbs_g=0,
            fat_g=5.4,
        ),
        MealItem(
            meal_id=meal1.id,
            name="Insalata mista",
            source="classification",
            confidence=0.82,
            estimated_grams=100,
            kcal=15,
            protein_g=1.4,
            carbs_g=2.9,
            fat_g=0.2,
        ),
    ]

    items2 = [
        MealItem(
            meal_id=meal2.id,
            name="Yogurt greco",
            source="manual",
            estimated_grams=125,
            kcal=121.25,
            protein_g=11.25,
            carbs_g=4.63,
            fat_g=6.25,
        ),
        MealItem(
            meal_id=meal2.id,
            name="Mandorle",
            source="manual",
            estimated_grams=30,
            kcal=173.7,
            protein_g=6.3,
            carbs_g=6.6,
            fat_g=15,
        ),
    ]

    for item in items1 + items2:
        db.add(item)

    db.commit()
    db.close()
    print("Seed data inserted successfully.")
    print(f"  Meal 1: Pasta pollo insalata ({now - timedelta(hours=3)})")
    print(f"  Meal 2: Yogurt mandorle ({now - timedelta(hours=8)})")


if __name__ == "__main__":
    seed()
