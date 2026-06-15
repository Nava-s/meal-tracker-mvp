import io
from typing import Optional

import cv2
import numpy as np

from services.nutrition_service import get_nutrition_for_food

AVERAGE_SERVINGS: dict[str, float] = {
    "pasta": 200,
    "rice": 180,
    "bread": 80,
    "pizza": 250,
    "soup": 250,
    "salad": 150,
    "vegetables": 150,
    "fruit": 150,
    "meat": 150,
    "chicken": 150,
    "fish": 150,
    "eggs": 120,
    "cheese": 60,
    "yogurt": 125,
    "dessert": 100,
    "cake": 100,
    "ice_cream": 100,
    "sauce": 50,
    "default": 150,
}


def _find_category(food_name: str) -> str:
    name_lower = food_name.lower().replace("_", " ")
    for cat_key in AVERAGE_SERVINGS:
        if cat_key in name_lower or name_lower in cat_key:
            return cat_key
    info = get_nutrition_for_food(food_name)
    if info:
        cat = info.get("category", "").lower()
        if cat:
            for cat_key in AVERAGE_SERVINGS:
                if cat_key in cat:
                    return cat_key
    return "default"


def _detect_plate_area_ratio(image_bytes: bytes) -> Optional[float]:
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        plate_area = cv2.contourArea(largest)
        total_area = h * w
        ratio = plate_area / total_area

        if ratio > 0.8 or ratio < 0.05:
            return None

        return ratio
    except Exception:
        return None


def estimate_portion(food_name: str, image_bytes: bytes) -> float:
    avg = AVERAGE_SERVINGS.get(_find_category(food_name), AVERAGE_SERVINGS["default"])

    plate_ratio = _detect_plate_area_ratio(image_bytes)
    if plate_ratio is not None:
        scaled = avg * (plate_ratio / 0.3)
        scaled = max(avg * 0.3, min(avg * 2.0, scaled))
        return round(scaled, 0)

    return avg
