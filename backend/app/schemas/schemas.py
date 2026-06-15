from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MealItemBase(BaseModel):
    name: str
    source: str = "manual"
    confidence: Optional[float] = None
    estimated_grams: float = 100.0
    kcal: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    barcode: Optional[str] = None
    external_product_id: Optional[str] = None


class MealItemCreate(MealItemBase):
    pass


class MealItemResponse(MealItemBase):
    id: int
    meal_id: int

    model_config = ConfigDict(from_attributes=True)


class MealBase(BaseModel):
    source_type: str = "manual"
    notes: Optional[str] = None


class MealCreate(MealBase):
    created_at: Optional[datetime] = None
    meal_label: Optional[str] = None
    items: list[MealItemCreate] = []


class MealUpdate(BaseModel):
    notes: Optional[str] = None
    meal_label: Optional[str] = None
    items: Optional[list[MealItemCreate]] = None


class MealResponse(MealBase):
    id: int
    created_at: datetime
    image_path: Optional[str] = None
    meal_label: Optional[str] = None
    items: list[MealItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DailySummary(BaseModel):
    date: str
    total_kcal: float = 0.0
    total_protein: float = 0.0
    total_carbs: float = 0.0
    total_fat: float = 0.0
    meals: list[MealResponse] = []


class BarcodeRequest(BaseModel):
    barcode: str


class BarcodeProduct(BaseModel):
    barcode: str
    name: str
    brand: Optional[str] = None
    nutriments_per_100g: dict = {}
    nutriments_per_serving: Optional[dict] = None
    serving_size: Optional[str] = None
    ingredients_text: Optional[str] = None
    source: str = "cache"


class AnalyzePhotoItem(BaseModel):
    name: str
    confidence: float
    estimated_grams: float
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class AnalyzePhotoResponse(BaseModel):
    items: list[AnalyzePhotoItem]


class FoodSearchResult(BaseModel):
    name: str
    brand: Optional[str] = None
    barcode: str
    nutriments_per_100g: dict = {}


class FoodSearchResponse(BaseModel):
    results: list[FoodSearchResult]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
