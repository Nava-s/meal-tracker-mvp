import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db, engine
from app.db.models import Base

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health():
    resp = client.get("/")
    assert resp.status_code in (200, 404)


def test_create_meal():
    resp = client.post("/api/meals", json={
        "source_type": "manual",
        "meal_label": "lunch",
        "items": [
            {"name": "Pasta", "source": "manual", "estimated_grams": 200, "kcal": 262, "protein_g": 10, "carbs_g": 50, "fat_g": 2.2},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] > 0
    assert data["meal_label"] == "lunch"
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Pasta"


def test_list_meals():
    client.post("/api/meals", json={
        "source_type": "manual",
        "items": [{"name": "Test", "estimated_grams": 100, "kcal": 100, "protein_g": 5, "carbs_g": 10, "fat_g": 3}],
    })
    resp = client.get("/api/meals")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1


def test_get_meal_not_found():
    resp = client.get("/api/meals/999")
    assert resp.status_code == 404


def test_update_meal():
    create = client.post("/api/meals", json={
        "source_type": "barcode",
        "items": [{"name": "Yogurt", "estimated_grams": 125, "kcal": 80, "protein_g": 4, "carbs_g": 10, "fat_g": 3}],
    }).json()
    meal_id = create["id"]

    resp = client.put(f"/api/meals/{meal_id}", json={
        "notes": "Modificato",
        "items": [{"name": "Yogurt greco", "estimated_grams": 200, "kcal": 120, "protein_g": 8, "carbs_g": 12, "fat_g": 4}],
    })
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Modificato"
    assert len(resp.json()["items"]) == 1


def test_delete_meal():
    create = client.post("/api/meals", json={
        "source_type": "manual",
        "items": [{"name": "Test", "estimated_grams": 100, "kcal": 100, "protein_g": 5, "carbs_g": 10, "fat_g": 3}],
    }).json()
    resp = client.delete(f"/api/meals/{create['id']}")
    assert resp.status_code == 200
    assert client.get(f"/api/meals/{create['id']}").status_code == 404


def test_daily_summary():
    client.post("/api/meals", json={
        "source_type": "manual",
        "items": [{"name": "Pasta", "estimated_grams": 200, "kcal": 262, "protein_g": 10, "carbs_g": 50, "fat_g": 2.2}],
    })
    from datetime import date
    today = date.today().isoformat()
    resp = client.get(f"/api/meals/daily-summary?date={today}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_kcal"] == 262
    assert data["total_protein"] == 10


def test_barcode_invalid():
    resp = client.post("/api/scan-barcode", json={"barcode": "0000000000000"})
    assert resp.status_code == 404


def test_analyze_photo_no_file():
    resp = client.post("/api/analyze-photo")
    assert resp.status_code == 422
