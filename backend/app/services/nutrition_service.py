import csv
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
NUTRITION_CSV = DATA_DIR / "nutrition_db.csv"

_nutrition_db: dict[str, dict] | None = None

_FOOD101_TO_ITALIAN: dict[str, str] = {
    "chicken_curry": "pollo arrosto",
    "chicken_wings": "pollo arrosto",
    "grilled_chicken": "pollo arrosto",
    "roasted_chicken": "pollo arrosto",
    "chicken_quesadilla": "pollo arrosto",
    "fried_chicken": "pollo arrosto",
    "chicken_tikka_masala": "pollo arrosto",
    "fried_rice": "riso",
    "beef_carpaccio": "carne di manzo",
    "beef_tartare": "carne di manzo",
    "bread_pudding": "pane bianco",
    "breakfast_burrito": "pizza",
    "bruschetta": "pane bianco",
    "caesar_salad": "insalata",
    "cannoli": "biscotti",
    "caprese_salad": "mozzarella",
    "carrot_cake": "torta",
    "cheese_plate": "formaggio",
    "cheesecake": "torta",
    "chocolate_cake": "cioccolato fondente",
    "chocolate_mousse": "cioccolato fondente",
    "clam_chowder": "zuppa",
    "club_sandwich": "pane bianco",
    "creme_brulee": "budino",
    "deviled_eggs": "uova sode",
    "donuts": "biscotti",
    "eggs_benedict": "uova strapazzate",
    "escargots": "pesce al forno",
    "filet_mignon": "bistecca di manzo",
    "fish_and_chips": "pesce al forno",
    "foie_gras": "pane bianco",
    "french_fries": "patate fritte",
    "french_onion_soup": "zuppa",
    "french_toast": "pane bianco",
    "fried_calamari": "pesce al forno",
    "greek_salad": "insalata",
    "grilled_cheese_sandwich": "formaggio",
    "grilled_salmon": "salmone",
    "hamburger": "hamburger",
    "hot_dog": "salsiccia",
    "huevos_rancheros": "uova strapazzate",
    "lobster_bisque": "zuppa",
    "lobster_roll_sandwich": "pesce al forno",
    "macaroni_and_cheese": "pasta",
    "mussels": "pesce al forno",
    "nachos": "pizza",
    "omelette": "uova strapazzate",
    "onion_rings": "patate fritte",
    "oysters": "pesce al forno",
    "pad_thai": "pasta",
    "paella": "riso",
    "pancakes": "biscotti",
    "panna_cotta": "budino",
    "peking_duck": "pollo arrosto",
    "pho": "zuppa",
    "pork_chop": "maiale",
    "poutine": "patate fritte",
    "prime_rib": "bistecca di manzo",
    "pulled_pork_sandwich": "maiale",
    "ramen": "pasta",
    "red_velvet_cake": "torta",
    "risotto": "riso",
    "samosa": "pizza",
    "scallops": "pesce al forno",
    "shrimp_and_grits": "gamberi",
    "spaghetti_bolognese": "spaghetti",
    "spaghetti_carbonara": "spaghetti",
    "steak": "bistecca di manzo",
    "stuffed_peppers": "peperoni",
    "sushi": "riso",
    "tacos": "pizza",
    "takoyaki": "pesce al forno",
    "tiramisu": "tiramisù",
    "tuna_tartare": "tonno",
    "waffles": "biscotti",
    "lasagna": "pasta",
    "gnocchi": "pasta",
    "ravioli": "pasta",
    "garlic_bread": "pane bianco",
    "pork_chop": "maiale",
    "hot_and_sour_soup": "zuppa",
    "miso_soup": "zuppa",
    "seaweed_salad": "insalata",
    "bibimbap": "riso",
    "beet_salad": "insalata",
    "beignets": "biscotti",
    "croque_madame": "pane bianco",
    "cup_cakes": "biscotti",
    "edamame": "fagiolini",
    "falafel": "pizza",
    "frozen_yogurt": "yogurt",
    "hummus": "olio d'oliva",
    "ice_cream": "gelato",
    "macarons": "biscotti",
    "baby_back_ribs": "maiale",
    "baklava": "biscotti",
    "spring_rolls": "pizza",
    "strawberry_shortcake": "torta",
    "apple_pie": "torta",
}


def _normalize(name: str) -> str:
    name = name.strip().lower().replace("_", " ")
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return name


def _load_nutrition_db() -> dict[str, dict]:
    global _nutrition_db
    if _nutrition_db is not None:
        return _nutrition_db
    _nutrition_db = {}
    if not NUTRITION_CSV.exists():
        return _nutrition_db
    with open(NUTRITION_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["name"].strip().lower()
            _nutrition_db[key] = {
                "name": row["name"].strip(),
                "category": row.get("category", "").strip(),
                "kcal_per_100g": float(row.get("kcal_per_100g", 0) or 0),
                "protein_per_100g": float(row.get("protein_per_100g", 0) or 0),
                "carbs_per_100g": float(row.get("carbs_per_100g", 0) or 0),
                "fat_per_100g": float(row.get("fat_per_100g", 0) or 0),
                "serving_g": float(row.get("serving_g", 100) or 100),
            }
    return _nutrition_db


def get_nutrition_for_food(food_name: str) -> dict | None:
    db = _load_nutrition_db()
    raw_key = food_name.strip().lower()

    mapped = _FOOD101_TO_ITALIAN.get(raw_key)
    if mapped:
        if mapped in db:
            return db[mapped]

    normalized = _normalize(food_name)
    if normalized in db:
        return db[normalized]

    for db_key, data in db.items():
        db_key_norm = _normalize(db_key)
        if db_key_norm in normalized or normalized in db_key_norm:
            return data

    return None


def search_foods(query: str, limit: int = 10) -> list[dict]:
    db = _load_nutrition_db()
    q = _normalize(query)
    results = []
    for key, data in db.items():
        if q in _normalize(key):
            results.append(data)
            if len(results) >= limit:
                break
    return results


def compute_nutrients(name: str, grams: float) -> dict:
    info = get_nutrition_for_food(name)
    if info is None:
        return {
            "name": name,
            "estimated_grams": grams,
            "kcal": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
        }
    factor = grams / 100.0
    return {
        "name": info["name"],
        "estimated_grams": grams,
        "kcal": round(info["kcal_per_100g"] * factor, 1),
        "protein_g": round(info["protein_per_100g"] * factor, 1),
        "carbs_g": round(info["carbs_per_100g"] * factor, 1),
        "fat_g": round(info["fat_per_100g"] * factor, 1),
    }
