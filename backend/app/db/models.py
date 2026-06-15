from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.db.database import Base


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_type = Column(String(20), nullable=False)  # 'photo' | 'barcode' | 'manual'
    image_path = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    meal_label = Column(String(20), nullable=True)  # 'breakfast' | 'snack' | 'lunch' | 'dinner'

    items = relationship("MealItem", back_populates="meal", cascade="all, delete-orphan",
                         order_by="MealItem.id")


class MealItem(Base):
    __tablename__ = "meal_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    source = Column(String(20), nullable=False)  # 'classification' | 'barcode' | 'manual'
    confidence = Column(Float, nullable=True)
    estimated_grams = Column(Float, nullable=False, default=100.0)
    kcal = Column(Float, nullable=False, default=0.0)
    protein_g = Column(Float, nullable=False, default=0.0)
    carbs_g = Column(Float, nullable=False, default=0.0)
    fat_g = Column(Float, nullable=False, default=0.0)
    barcode = Column(String(50), nullable=True)
    external_product_id = Column(String(200), nullable=True)

    meal = relationship("Meal", back_populates="items")


class ProductCache(Base):
    __tablename__ = "products_cache"

    barcode = Column(String(50), primary_key=True)
    name = Column(String(300), nullable=False)
    brand = Column(String(200), nullable=True)
    nutriments = Column(JSON, nullable=True)
    ingredients_text = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
