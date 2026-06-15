# AGENTS.md - Meal Tracker

## Comandi

- **Avvio backend**: `cd backend && uvicorn app.main:app --reload --port 8000`
- **Test**: `cd backend && pytest tests/ -v`
- **Seed data**: `cd backend && python -m seed_data`
- **Docker**: `docker-compose up --build`

## Convenzioni codice

- No commenti (salvo docstring necessarie)
- Type hints su funzioni pubbliche
- Moduli separati per layer: api/, services/, ml/, db/, schemas/
- Modelli SQLAlchemy in app/db/models.py
- Schemi Pydantic in app/schemas/schemas.py
- Logica di business in app/services/
- ML in app/ml/

## Struttura

- Ogni router FastAPI in app/api/*.py
- Tutti i router importati in app/main.py
- Frontend vanilla JS in frontend/
- DB SQLite auto-creato in backend/data/meal_tracker.db
