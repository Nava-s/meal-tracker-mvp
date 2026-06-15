from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.schemas import AnalyzePhotoResponse, AnalyzePhotoItem
from app.ml.food_classifier import classify_food_image
from app.ml.portion_estimator import estimate_portion
from app.services.nutrition_service import compute_nutrients

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze-photo", response_model=AnalyzePhotoResponse)
async def analyze_photo(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(400, "Empty file")

    classifications = await classify_food_image(image_bytes)
    if not classifications:
        return AnalyzePhotoResponse(items=[])

    items = []
    for food_name, confidence in classifications:
        portion_grams = estimate_portion(food_name, image_bytes)
        nutrients = compute_nutrients(food_name, portion_grams)
        items.append(AnalyzePhotoItem(
            name=nutrients["name"],
            confidence=round(confidence, 3),
            estimated_grams=nutrients["estimated_grams"],
            kcal=nutrients["kcal"],
            protein_g=nutrients["protein_g"],
            carbs_g=nutrients["carbs_g"],
            fat_g=nutrients["fat_g"],
        ))

    return AnalyzePhotoResponse(items=items)
