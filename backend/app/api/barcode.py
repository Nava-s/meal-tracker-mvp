from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schemas import BarcodeRequest, BarcodeProduct, FoodSearchResponse, FoodSearchResult
from app.services.barcode_service import lookup_barcode, search_products

router = APIRouter(prefix="/api", tags=["barcode"])


@router.post("/scan-barcode", response_model=BarcodeProduct)
async def scan_barcode(payload: BarcodeRequest, db: Session = Depends(get_db)):
    result = await lookup_barcode(payload.barcode, db)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail=result.get("error", "Barcode not found"))
    return BarcodeProduct(
        barcode=result["barcode"],
        name=result["name"],
        brand=result.get("brand"),
        nutriments_per_100g=result.get("nutriments_per_100g", {}),
        nutriments_per_serving=result.get("nutriments_per_serving"),
        serving_size=result.get("serving_size"),
        ingredients_text=result.get("ingredients_text"),
        source=result.get("source", "cache"),
    )


@router.get("/foods/search", response_model=FoodSearchResponse)
def search_foods(query: str, db: Session = Depends(get_db)):
    results = search_products(query, db)
    return FoodSearchResponse(
        results=[
            FoodSearchResult(
                name=r["name"],
                brand=r.get("brand"),
                barcode=r["barcode"],
                nutriments_per_100g=r.get("nutriments_per_100g", {}),
            )
            for r in results
        ]
    )
