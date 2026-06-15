from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from db.models import ProductCache

OPENFOODFACTORS_API = "https://world.openfoodfacts.org/api/v2/product"


def lookup_barcode(barcode: str, db: Session) -> dict:
    cached = db.query(ProductCache).filter(ProductCache.barcode == barcode).first()
    if cached:
        return _product_to_dict(cached, source="cache")

    try:
        resp = httpx.get(f"{OPENFOODFACTORS_API}/{barcode}.json", timeout=10.0)
        if resp.status_code != 200:
            return {"found": False, "barcode": barcode,
                    "error": "Product not found on Open Food Facts"}
        data = resp.json()
        product = data.get("product")
        if not product:
            return {"found": False, "barcode": barcode,
                    "error": "No product data returned"}
        nutriments = product.get("nutriments", {})
        per_100g = _extract_per_100g(nutriments)

        entry = ProductCache(
            barcode=barcode,
            name=product.get("product_name", "Unknown product"),
            brand=product.get("brands"),
            nutriments=nutriments,
            ingredients_text=product.get("ingredients_text", ""),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()

        return {
            "found": True,
            "barcode": barcode,
            "name": entry.name,
            "brand": entry.brand,
            "nutriments_per_100g": per_100g,
            "ingredients_text": entry.ingredients_text,
            "source": "openfoodfacts",
        }
    except httpx.RequestError as e:
        return {"found": False, "barcode": barcode,
                "error": f"Network error: {str(e)}"}


def search_products(query: str, db: Session, limit: int = 10) -> list[dict]:
    results = db.query(ProductCache).filter(
        ProductCache.name.ilike(f"%{query}%")
    ).limit(limit).all()
    return [_product_to_dict(p, source="cache") for p in results]


def _extract_per_100g(n: dict) -> dict:
    return {
        "energy_kcal": n.get("energy-kcal_100g") or n.get("energy_100g", 0),
        "protein": n.get("proteins_100g", 0),
        "carbohydrates": n.get("carbohydrates_100g", 0),
        "fat": n.get("fat_100g", 0),
        "fiber": n.get("fiber_100g", 0),
        "salt": n.get("salt_100g", 0),
        "saturated_fat": n.get("saturated-fat_100g", 0),
        "sugars": n.get("sugars_100g", 0),
    }


def _product_to_dict(p: ProductCache, source: str = "cache") -> dict:
    per_100g = _extract_per_100g(p.nutriments or {})
    return {
        "found": True,
        "barcode": p.barcode,
        "name": p.name,
        "brand": p.brand,
        "nutriments_per_100g": per_100g,
        "ingredients_text": p.ingredients_text,
        "source": source,
    }
