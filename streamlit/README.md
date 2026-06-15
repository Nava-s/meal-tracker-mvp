# Meal Tracker — Streamlit

App personale per tracciare pasti. Backend + Frontend in un unico file Python con Streamlit.

## Avvio rapido

```bash
cd streamlit
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
streamlit run app.py
```

Si apre su `http://localhost:8501`. Dal telefono, connettiti allo stesso Wi-Fi e vai su `http://IP-DEL-PC:8501`.

## Funzionalità

- **📷 Analizza Foto**: scatta o carica una foto, il modello ML classifica il cibo, stima la porzione e calcola i nutrienti. Modifica tutto prima di salvare.
- **📱 Scansiona Barcode**: scatta un barcode con la fotocamera del telefono (OpenCV nativo) o digita il codice. Lookup su Open Food Facts con cache locale.
- **📓 Diario**: riepilogo giornaliero con totali kcal/macros. Elimina pasti con un click.
- **💾 Salvataggio**: ogni pasto ha data/ora, etichetta (colazione/snack/pranzo/cena) e note opzionali.

## Struttura

```
streamlit/
├── app.py                 # Applicazione principale (UI + logica)
├── db/
│   ├── database.py        # Connessione SQLite
│   └── models.py          # Modelli SQLAlchemy (Meal, MealItem, ProductCache)
├── services/
│   ├── nutrition_service.py   # Database nutrizionale + lookup
│   └── barcode_service.py     # Open Food Facts + cache
├── ml/
│   ├── food_classifier.py     # Classificazione cibo (HuggingFace)
│   └── portion_estimator.py   # Stima porzione (OpenCV + euristica)
├── data/
│   ├── nutrition_db.csv       # ~80 alimenti con valori per 100g
│   └── meal_tracker.db        # SQLite (auto-creato)
├── .streamlit/
│   └── config.toml            # Configurazione (server 0.0.0.0)
└── requirements.txt
```

## Note tecniche

- **Classificazione foto**: usa `nateraw/food` (ResNet50 su Food-101, ~100MB). Se non installato, l'inserimento manuale è sempre disponibile.
- **Barcode**: OpenCV `BarcodeDetector` nativo. Nessuna dipendenza esterna.
- **Database**: SQLite locale. I dati non escono mai dal tuo computer.
- **PyTorch**: serve per la classificazione foto. Per l'inserimento manuale e il barcode non è necessario.
