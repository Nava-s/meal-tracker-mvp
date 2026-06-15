# Meal Tracker su Android

Due modalità: **locale** (server + browser sullo stesso telefono) o **server casalingo** (backed su PC, frontend via browser su telefono).

## Modalità A — Locale (Termux + PWA)

Il telefono fa tutto: backend e browser.

### Prerequisiti
- [Termux](https://termux.dev/) (F-Droid, **non** Google Play — versione obsoleta)
- [Termux:API](https://f-droid.org/packages/com.termux.api/) (per storage)

### Installazione rapida

```bash
# Copia android/ nel telefono (via USB/cable/cloud) oppure clona il repo in Termux
# Poi:
cd android
chmod +x termux-setup.sh
./termux-setup.sh
```

Lo script fa tutto automaticamente:
1. Installa Python, OpenCV e dipendenze di sistema
2. Crea virtualenv e installa le librerie Python (esclusi torch/transformers)
3. Copia backend/ e frontend/ in `~/meal-tracker`
4. Crea script di avvio `start.sh` e `start-network.sh`

### Avvio

```bash
cd ~/meal-tracker
./start.sh
# Apri http://localhost:8000 in Chrome
# Menu Chrome → Aggiungi a schermata Home → si apre come app
```

### Foto con classificazione automatica (opzionale, ~300MB extra)

```bash
source ~/meal-tracker/backend/venv/bin/activate
pip install torch torchvision transformers
python -c "from app.ml.food_classifier import _load_model; _load_model(); print('OK')"
```

### Barcode scanner
Funziona via Chrome (libreria `html5-qrcode` via CDN). Concede il permesso camera quando richiesto.

## Modalità B — Server su PC, client su telefono

Backend su PC, frontend su Android via browser.

### Sul PC (una tantum)
```bash
git clone <questo-repo> meal-tracker
cd meal-tracker/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m seed_data  # dati di test
```

### Sul PC (avvio server)
```bash
cd meal-tracker/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Sul telefono
- Chrome → `http://IP-DEL-PC:8000`
- Aggiungi a schermata Home

## Limitazioni note su Android (Termux)
- **PyTorch**: OpenCV + PyTorch insieme occupano ~500MB. Per MVP, l'app funziona anche senza (classificazione foto → inserimento manuale). Installa torch solo se hai spazio.
- **Avvio automatico**: Termux non ha avvio automatico del server. Va lanciato manualmente ogni volta. Esistono workaround (Termux:Boot) ma non banali.
- **Fotocamera**: La foto viene scattata dal browser (Chrome cattura `capture="environment"`). Funziona bene.
- **Batteria**: Il server in background consuma batteria. Conviene fermarlo con `Ctrl+C` quando non usato.
