# Meal Tracker

App personale per tracciare pasti tramite foto e codici a barre.

## Stack

- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **Food Classifier**: `nateraw/food` (ResNet50 su Food-101) via HuggingFace Transformers
- **Barcode**: Open Food Facts API + cache locale SQLite
- **Frontend**: Vanilla JS SPA + PWA (mobile-first)
- **Container**: Docker / Docker Compose

## Avvio rapido (locale)

### Prerequisiti

- Python 3.10+
- (Opzionale) Docker + Docker Compose

### Installazione

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

### Avvio backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Il backend parte su `http://localhost:8000`.  
Il frontend è servito automaticamente alla stessa URL.

### Seed dati di test

```bash
cd backend
python -m seed_data
```

### Test

```bash
cd backend
pytest tests/ -v
```

### Docker

```bash
docker-compose up --build
```

## Struttura progetto

```
meal-tracker/
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoint FastAPI
│   │   ├── services/      # Barcode + Nutrition logic
│   │   ├── ml/            # Food classifier + portion estimator
│   │   ├── db/            # SQLAlchemy models + database
│   │   ├── schemas/       # Pydantic schemas
│   │   └── main.py        # App entry point
│   ├── data/
│   │   ├── nutrition_db.csv   # ~80 alimenti con valori per 100g
│   │   └── meal_tracker.db    # SQLite database (auto-creato)
│   ├── tests/
│   ├── seed_data.py
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── css/app.css
│   ├── js/
│   │   ├── app.js         # SPA main (routing, state, views)
│   │   ├── api.js         # Fetch wrapper
│   │   ├── scanner.js     # Barcode scanner (html5-qrcode)
│   │   └── camera.js      # Camera access
│   ├── manifest.json
│   └── sw.js              # Service Worker
├── docker-compose.yml
└── README.md
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/analyze-photo` | Analizza foto pasto |
| POST | `/api/scan-barcode` | Cerca prodotto per barcode |
| GET | `/api/foods/search?query=...` | Cerca prodotti in cache |
| POST | `/api/meals` | Crea pasto |
| GET | `/api/meals` | Lista pasti |
| GET | `/api/meals/{id}` | Dettaglio pasto |
| PUT | `/api/meals/{id}` | Modifica pasto |
| DELETE | `/api/meals/{id}` | Elimina pasto |
| GET | `/api/meals/daily-summary?date=YYYY-MM-DD` | Riepilogo giornaliero |

## Schema DB

- **meals**: id, created_at, source_type, image_path, notes
- **meal_items**: id, meal_id, name, source, confidence, estimated_grams, kcal, protein_g, carbs_g, fat_g, barcode, external_product_id
- **products_cache**: barcode, name, brand, nutriments (JSON), ingredients_text, updated_at

## Limitazioni MVP note

1. **Food classification**: Il modello `nateraw/food` classifica tra 101 categorie Food-101. Può sbagliare. Usare la correzione manuale.
2. **Porzione**: Stima euristica basata su media per categoria + rilevamento area piatto (OpenCV). Non precisa. Correggere sempre manualmente.
3. **Segmentazione**: Non implementata nell'MVP. L'intera immagine viene classificata come un singolo alimento.
4. **Nutrizione**: Il database CSV copre ~80 alimenti comuni. Per alimenti non presenti, i valori sono zero (correggere manualmente).

## Prossimi miglioramenti

- Segmentazione alimenti (detection invece che classification)
- Migliore stima porzioni (riferimento scala, depth estimation)
- Database nutrizionale più ricco
- Export dati
- Grafici trend settimanali
