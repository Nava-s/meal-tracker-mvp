#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "📦 Meal Tracker - Termux Setup"
echo "==============================="

# 1. Aggiorna pkg e installa dipendenze di sistema
echo ""
echo "[1/5] Aggiorno pkg e installo dipendenze di sistema..."
pkg update -y
pkg upgrade -y
pkg install -y python tur-repo x11-repo
pkg install -y opencv-python-headless binutils rust binutils-is-llvm

# 2. Permessi storage per salvare foto
echo ""
echo "[2/5] Abilito accesso storage..."
termux-setup-storage

# 3. Crea directory progetto
echo ""
echo "[3/5] Copio i file del progetto..."
MEAL_DIR="$HOME/meal-tracker"
mkdir -p "$MEAL_DIR"

# Se eseguito dalla directory android, copia da ..
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -d "$PROJECT_DIR/backend" ]; then
    cp -r "$PROJECT_DIR/backend" "$MEAL_DIR/"
    cp -r "$PROJECT_DIR/frontend" "$MEAL_DIR/"
    echo "   File copiati da $PROJECT_DIR"
else
    echo "   ERRORE: esegui questo script dalla cartella android/ del progetto"
    exit 1
fi

# 4. Crea virtualenv e installa dipendenze Python
echo ""
echo "[4/5] Creo virtualenv e installo dipendenze Python..."
cd "$MEAL_DIR/backend"
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install wheel setuptools

# Installa solo quello che serve per MVP (senza torch/transformers per risparmiare spazio)
echo ""
echo "   Installazione dipendenze core..."
pip install fastapi uvicorn sqlalchemy pydantic python-multipart httpx opencv-python-headless Pillow aiofiles python-dateutil

echo ""
echo "   NOTA: PyTorch + Transformers (~200MB) NON vengono installati automaticamente."
echo "   L'app funzionerà comunque con inserimento manuale degli alimenti."
echo "   Per abilitare la classificazione foto, esegui dopo:"
echo "       source ~/meal-tracker/backend/venv/bin/activate"
echo "       pip install torch torchvision transformers"
echo "       python -c \"from app.ml.food_classifier import _load_model; print('Modello scaricato')\""

# 5. Crea script di avvio
echo ""
echo "[5/5] Creo script di avvio..."
cat > "$HOME/meal-tracker/start.sh" << 'STARTEOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/meal-tracker/backend
source venv/bin/activate
echo "🍽️  Avvio Meal Tracker..."
echo "   Apri Chrome e vai a: http://localhost:8000"
echo "   (Ctrl+C per fermare)"
echo ""
uvicorn app.main:app --host 127.0.0.1 --port 8000
STARTEOF
chmod +x "$HOME/meal-tracker/start.sh"

# Crea anche uno script per avvio con hotspot
cat > "$HOME/meal-tracker/start-network.sh" << 'NETEOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/meal-tracker/backend
source venv/bin/activate
# Ottieni IP del telefono
IP=$(ip -4 addr show wlan0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' || echo "0.0.0.0")
echo "🍽️  Meal Tracker in rete"
echo "   Server: $IP:8000"
echo "   Da qualsiasi dispositivo nella stessa rete:"
echo "   http://$IP:8000"
echo ""
uvicorn app.main:app --host 0.0.0.0 --port 8000
NETEOF
chmod +x "$HOME/meal-tracker/start-network.sh"

# Crea file README per Android
cat > "$HOME/meal-tracker/README.md" << 'READMEEOF'
# Meal Tracker su Android

## Avvio

1. Apri Termux
2. Esegui:
   ```bash
   cd ~/meal-tracker
   ./start.sh
   ```
3. Apri Chrome, vai a `http://localhost:8000`
4. (Opzionale) Aggiungi a schermata Home dal menu di Chrome

## Per usare da PC nella stessa rete

```bash
cd ~/meal-tracker
./start-network.sh
```
Poi dal PC apri `http://IP-DEL-TELEFONO:8000`

## Foto analytics (opzionale)

Per abilitare il riconoscimento automatico degli alimenti:
```bash
source ~/meal-tracker/backend/venv/bin/activate
pip install torch torchvision transformers
python -c "from app.ml.food_classifier import _load_model; _load_model(); print('OK')"
```
Il modello viene scaricato la prima volta (~100MB).

## Comandi utili

- Fermare server: `Ctrl+C`
- Seed dati di test: `cd ~/meal-tracker/backend && source venv/bin/activate && python -m seed_data`
- Reset DB: `rm ~/meal-tracker/backend/data/meal_tracker.db`
READMEEOF

echo ""
echo "✅ Installazione completata!"
echo ""
echo "📱 Per avviare:"
echo "   cd ~/meal-tracker"
echo "   ./start.sh"
echo ""
echo "   Poi apri http://localhost:8000 in Chrome"
echo "   (Aggiungi a Schermata Home per esperienza app-like)"
echo ""
