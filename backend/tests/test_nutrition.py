from app.services.nutrition_service import get_nutrition_for_food, compute_nutrients, search_foods


def test_lookup_pizza():
    result = get_nutrition_for_food("pizza")
    assert result is not None
    assert result["kcal_per_100g"] > 200


def test_lookup_pizza_margherita():
    result = get_nutrition_for_food("Pizza margherita")
    assert result is not None
    assert result["kcal_per_100g"] > 200


def test_lookup_spaghetti():
    result = get_nutrition_for_food("Spaghetti")
    assert result is not None
    assert result["kcal_per_100g"] > 100
    assert result["protein_per_100g"] > 4


def test_lookup_underscore_spaghetti():
    """Food-101 labels use underscores"""
    result = get_nutrition_for_food("spaghetti_bolognese")
    assert result is not None
    assert result["kcal_per_100g"] > 100


def test_lookup_english_chicken_curry():
    """English label with no direct CSV match"""
    result = get_nutrition_for_food("chicken_curry")
    assert result is not None
    assert result["kcal_per_100g"] > 100


def test_lookup_tiramisu():
    """Accent normalization: tiramisu -> tiramisù"""
    result = get_nutrition_for_food("tiramisu")
    assert result is not None
    assert result["kcal_per_100g"] > 200


def test_compute_nutrients_pizza():
    result = compute_nutrients("pizza", 250)
    assert result["kcal"] > 500
    assert result["protein_g"] > 20
    assert result["estimated_grams"] == 250


def test_compute_nutrients_english_label():
    """chicken_curry should map to pollo arrosto via synonym dict"""
    result = compute_nutrients("chicken_curry", 150)
    assert result["kcal"] > 0
    assert result["protein_g"] > 0


def test_compute_nutrients_unknown():
    """Unknown food returns zeros"""
    result = compute_nutrients("zzz_not_a_food_xyz", 100)
    assert result["kcal"] == 0
    assert result["protein_g"] == 0
    assert result["carbs_g"] == 0
    assert result["fat_g"] == 0


def test_search_foods_pasta():
    results = search_foods("pasta")
    assert len(results) > 0
    assert any("Pasta" in r["name"] for r in results)
