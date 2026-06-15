import { api } from "./api.js";
import { initScanner, stopScanner } from "./scanner.js";
import { initCamera } from "./camera.js";

let state = {
  currentView: "home",
  date: new Date().toISOString().slice(0, 10),
  meals: [],
  dailyTotals: null,
  scannedProduct: null,
  analyzeResults: null,
  pendingItems: [],
  editingMeal: null,
};

function navigate(hash) {
  stopScanner();
  const [view, ...params] = hash.replace(/^#\/?/, "").split("/");
  state.currentView = view || "home";

  document.querySelectorAll(".view").forEach((el) => el.classList.remove("active"));
  const target = document.getElementById(`view-${state.currentView}`);
  if (target) target.classList.add("active");

  switch (state.currentView) {
    case "home": renderHome(); break;
    case "scan": renderScan(); break;
    case "photo": renderPhoto(); break;
    case "diary": loadDiary(); break;
    case "meal": loadMeal(params[0]); break;
  }
}

window.addEventListener("hashchange", () => navigate(window.location.hash));
window.addEventListener("load", () => navigate(window.location.hash || "#home"));

function $(id) { return document.getElementById(id); }

function formatTime(d) {
  return new Date(d).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

function formatDateTimeLocal(d) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function round(v) { return Math.round(v * 10) / 10 || 0; }

function showToast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2500);
}

const LABELS = [
  { value: "breakfast", label: "Colazione" },
  { value: "snack", label: "Snack" },
  { value: "lunch", label: "Pranzo" },
  { value: "dinner", label: "Cena" },
];

function sourceIcon(t) {
  return t === "photo" ? "📷" : t === "barcode" ? "📱" : "✏️";
}

// --- Home ---
function renderHome() {
  const container = $("view-home");
  container.innerHTML = `
    <div class="hero">
      <h1>🍽️ Meal Tracker</h1>
      <p>Traccia i tuoi pasti con foto o codice a barre</p>
    </div>
    <div class="home-actions">
      <button class="btn btn-primary btn-large" onclick="location.hash='#photo'">📷 Analizza foto</button>
      <button class="btn btn-secondary btn-large" onclick="location.hash='#scan'">📱 Scansiona barcode</button>
      <button class="btn btn-outline btn-large" onclick="location.hash='#diary'">📓 Diario giornaliero</button>
    </div>
    <div class="quick-totals" id="quick-totals"></div>
  `;
  loadQuickTotals();
}

async function loadQuickTotals() {
  try {
    const summary = await api.dailySummary(state.date);
    const el = $("quick-totals");
    el.innerHTML = `
      <div class="totals-card">
        <span class="totals-date">${state.date}</span>
        <div class="totals-row">
          <span>🔥 ${round(summary.total_kcal)} kcal</span>
          <span>🥩 ${round(summary.total_protein)}g</span>
          <span>🍚 ${round(summary.total_carbs)}g</span>
          <span>🧈 ${round(summary.total_fat)}g</span>
        </div>
      </div>`;
  } catch {}
}

// --- Scan Barcode ---
function renderScan() {
  const container = $("view-scan");
  container.innerHTML = `
    <div class="view-header">
      <button class="btn-back" onclick="location.hash='#home'">←</button>
      <h2>Scansiona codice a barre</h2>
    </div>
    <div class="scanner-wrapper">
      <div id="scanner-view"></div>
      <p class="hint">Inquadra un codice a barre con la fotocamera</p>
    </div>
    <div class="manual-barcode">
      <p class="hint">Oppure inserisci il codice manualmente:</p>
      <div class="input-row">
        <input type="text" id="manual-barcode-input" placeholder="Codice a barre..." />
        <button class="btn btn-primary" id="manual-barcode-btn">Cerca</button>
      </div>
    </div>
    <div id="barcode-result"></div>
  `;
  initScanner((barcode) => handleBarcode(barcode));
  $("manual-barcode-btn").onclick = () => {
    const val = $("manual-barcode-input").value.trim();
    if (val) handleBarcode(val);
  };
}

async function handleBarcode(barcode) {
  const resultEl = $("barcode-result");
  resultEl.innerHTML = `<p class="loading">Cerco prodotto ${barcode}...</p>`;
  try {
    const product = await api.scanBarcode(barcode);
    const kcal100 = round(product.nutriments_per_100g.energy_kcal || 0);
    const p100 = round(product.nutriments_per_100g.protein || 0);
    const c100 = round(product.nutriments_per_100g.carbohydrates || 0);
    const f100 = round(product.nutriments_per_100g.fat || 0);
    state.scannedProduct = product;
    resultEl.innerHTML = `
      <div class="product-card">
        <h3>${product.name}</h3>
        ${product.brand ? `<p class="brand">${product.brand}</p>` : ""}
        <div class="nutrients">
          <span>🔥 ${kcal100} kcal/100g</span>
          <span>🥩 ${p100}g</span>
          <span>🍚 ${c100}g</span>
          <span>🧈 ${f100}g</span>
        </div>
        <div class="quantity-row">
          <label>Quantità (g):</label>
          <input type="number" class="barcode-grams" value="100" min="1" max="5000"
            data-kcal100="${kcal100}" data-p100="${p100}" data-c100="${c100}" data-f100="${f100}" />
        </div>
        <div class="recap-nutrients" id="barcode-recap">
          <strong>${kcal100} kcal</strong> · P ${p100}g · C ${c100}g · F ${f100}g
        </div>
        <div class="meal-metadata">
          <input type="datetime-local" class="meal-datetime" value="${formatDateTimeLocal(new Date())}" />
          <div class="label-group">
            ${LABELS.map(l => `<label class="label-btn"><input type="radio" name="barcode-label" value="${l.value}" /> ${l.label}</label>`).join("")}
          </div>
        </div>
        <button class="btn btn-primary" id="barcode-save">Salva nel diario</button>
      </div>
    `;
    resultEl.querySelector(".barcode-grams").oninput = recalcBarcode;
    $("barcode-save").onclick = () => saveBarcodeMeal();
  } catch (err) {
    resultEl.innerHTML = `
      <div class="not-found">
        <p>❌ Prodotto non trovato: ${barcode}</p>
        <p class="hint">Puoi inserire i dati manualmente.</p>
        <button class="btn btn-outline" onclick="location.hash='#diary'">Vai al diario</button>
      </div>`;
  }
}

function recalcBarcode() {
  const input = document.querySelector(".barcode-grams");
  const grams = parseFloat(input.value) || 0;
  const factor = grams / 100;
  const kcal = round(input.dataset.kcal100 * factor);
  const p = round(input.dataset.p100 * factor);
  const c = round(input.dataset.c100 * factor);
  const f = round(input.dataset.f100 * factor);
  document.getElementById("barcode-recap").innerHTML =
    `<strong>${kcal} kcal</strong> · P ${p}g · C ${c}g · F ${f}g`;
}

async function saveBarcodeMeal() {
  const input = document.querySelector(".barcode-grams");
  const grams = parseFloat(input.value) || 100;
  const factor = grams / 100;
  const kcal100 = parseFloat(input.dataset.kcal100) || 0;
  const p100 = parseFloat(input.dataset.p100) || 0;
  const c100 = parseFloat(input.dataset.c100) || 0;
  const f100 = parseFloat(input.dataset.f100) || 0;
  const product = state.scannedProduct;

  let dt = document.querySelector(".meal-datetime")?.value;
  const labelRadio = document.querySelector('input[name="barcode-label"]:checked');
  const label = labelRadio?.value || null;

  try {
    await api.createMeal({
      source_type: "barcode",
      meal_label: label,
      created_at: dt ? new Date(dt).toISOString() : undefined,
      items: [{
        name: product.name,
        source: "barcode",
        barcode: product.barcode,
        estimated_grams: grams,
        kcal: round(kcal100 * factor),
        protein_g: round(p100 * factor),
        carbs_g: round(c100 * factor),
        fat_g: round(f100 * factor),
        external_product_id: product.barcode,
      }],
    });
    showToast("✅ Pasto salvato!");
    state.scannedProduct = null;
    setTimeout(() => navigate("#diary"), 500);
  } catch (err) {
    showToast("❌ Errore: " + err.message);
  }
}

// --- Photo ---
function renderPhoto() {
  const container = $("view-photo");
  container.innerHTML = `
    <div class="view-header">
      <button class="btn-back" onclick="location.hash='#home'">←</button>
      <h2>Analizza foto</h2>
    </div>
    <div class="photo-upload">
      <div class="drop-zone" id="drop-zone"><p>📷 Clicca per scattare o caricare una foto</p></div>
      <input type="file" id="photo-input" accept="image/*" capture="environment" hidden />
    </div>
    <div id="photo-result"></div>
  `;
  $("drop-zone").onclick = () => $("photo-input").click();
  $("photo-input").onchange = () => {
    const file = $("photo-input").files?.[0];
    if (file) analyzePhoto(file);
  };
}

async function analyzePhoto(file) {
  const resultEl = $("photo-result");
  resultEl.innerHTML = `<p class="loading">Analizzo l'immagine...</p>`;
  const reader = new FileReader();
  reader.onload = (e) => {
    const img = document.createElement("img");
    img.src = e.target.result;
    img.className = "preview-img";
    resultEl.prepend(img);
  };
  reader.readAsDataURL(file);
  try {
    const result = await api.analyzePhoto(file);
    if (!result.items || result.items.length === 0) {
      resultEl.innerHTML += `<div class="empty-state"><p>Nessun alimento riconosciuto.</p><p class="hint">Aggiungi manualmente.</p><button class="btn btn-outline" onclick="addPhotoItem()">Aggiungi alimento</button></div>`;
      state.analyzeResults = [];
      return;
    }
    state.analyzeResults = result.items;
    renderPhotoReview();
  } catch (err) {
    resultEl.innerHTML += `<p class="error">❌ Errore: ${err.message}</p>`;
  }
}

function renderPhotoReview() {
  const items = state.analyzeResults || [];
  const resultEl = $("photo-result");
  let html = `<div class="review-section"><h3>Alimenti</h3><p class="hint">Le stime sono approssimative. Modifica i campi e rivedi prima di salvare.</p>`;

  items.forEach((item, i) => {
    const kcal100 = item.estimated_grams > 0 ? round((item.kcal || 0) / item.estimated_grams * 100) : 0;
    const name = item.confidence && item.confidence > 0 ? `${item.name} (${round(item.confidence * 100)}%)` : item.name;
    html += `
      <div class="item-card review-item" data-idx="${i}">
        <div class="item-header">
          <span class="item-name">${name}</span>
        </div>
        <div class="item-fields">
          <label>Nome: <input type="text" class="field-name" value="${item.name}" /></label>
          <label>Grammi: <input type="number" class="field-grams" value="${item.estimated_grams}" min="1"
            data-kcal100="${kcal100}" data-p100="${round(item.estimated_grams > 0 ? (item.protein_g || 0) / item.estimated_grams * 100 : 0)}"
            data-c100="${round(item.estimated_grams > 0 ? (item.carbs_g || 0) / item.estimated_grams * 100 : 0)}"
            data-f100="${round(item.estimated_grams > 0 ? (item.fat_g || 0) / item.estimated_grams * 100 : 0)}" /></label>
          <label>Kcal: <input type="number" class="field-kcal" value="${round(item.kcal)}" step="0.1" /></label>
          <label>Proteine: <input type="number" class="field-protein" value="${round(item.protein_g)}" step="0.1" /></label>
          <label>Carbs: <input type="number" class="field-carbs" value="${round(item.carbs_g)}" step="0.1" /></label>
          <label>Grassi: <input type="number" class="field-fat" value="${round(item.fat_g)}" step="0.1" /></label>
        </div>
        <button class="btn btn-danger btn-sm remove-photo-item" data-idx="${i}">Rimuovi</button>
      </div>`;
  });

  html += `
    <button class="btn btn-outline btn-sm" onclick="addPhotoItem()">+ Aggiungi alimento</button>
    <div class="meal-metadata mt-16">
      <label>Data/ora pasto:</label>
      <input type="datetime-local" class="meal-datetime" value="${formatDateTimeLocal(new Date())}" />
      <div class="label-group">
        ${LABELS.map(l => `<label class="label-btn"><input type="radio" name="photo-label" value="${l.value}" /> ${l.label}</label>`).join("")}
      </div>
    </div>
    <button class="btn btn-primary btn-large mt-16" id="save-photo-meal">Salva pasto</button>
  `;

  resultEl.innerHTML = html;

  resultEl.querySelectorAll(".field-grams").forEach((el) => el.oninput = recalcFromGrams);
  resultEl.querySelectorAll(".remove-photo-item").forEach((btn) => {
    btn.onclick = () => {
      state.analyzeResults.splice(parseInt(btn.dataset.idx), 1);
      renderPhotoReview();
    };
  });
  $("save-photo-meal")?.addEventListener("click", savePhotoMeal);
}

function recalcFromGrams(e) {
  const card = e.target.closest(".review-item");
  const grams = parseFloat(e.target.value) || 0;
  const factor = grams / 100;
  const kcal100 = parseFloat(e.target.dataset.kcal100) || 0;
  const p100 = parseFloat(e.target.dataset.p100) || 0;
  const c100 = parseFloat(e.target.dataset.c100) || 0;
  const f100 = parseFloat(e.target.dataset.f100) || 0;
  card.querySelector(".field-kcal").value = round(kcal100 * factor);
  card.querySelector(".field-protein").value = round(p100 * factor);
  card.querySelector(".field-carbs").value = round(c100 * factor);
  card.querySelector(".field-fat").value = round(f100 * factor);
}

window.addPhotoItem = function () {
  if (!state.analyzeResults) state.analyzeResults = [];
  state.analyzeResults.push({ name: "Nuovo alimento", confidence: 0, estimated_grams: 100, kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 });
  renderPhotoReview();
};

async function savePhotoMeal() {
  const items = [];
  document.querySelectorAll(".review-item").forEach((card) => {
    items.push({
      name: card.querySelector(".field-name").value,
      source: "classification",
      confidence: 0.5,
      estimated_grams: parseFloat(card.querySelector(".field-grams").value) || 100,
      kcal: parseFloat(card.querySelector(".field-kcal").value) || 0,
      protein_g: parseFloat(card.querySelector(".field-protein").value) || 0,
      carbs_g: parseFloat(card.querySelector(".field-carbs").value) || 0,
      fat_g: parseFloat(card.querySelector(".field-fat").value) || 0,
    });
  });

  if (items.length === 0) { showToast("Aggiungi almeno un alimento"); return; }

  let dt = document.querySelector(".meal-datetime")?.value;
  const labelRadio = document.querySelector('input[name="photo-label"]:checked');
  const label = labelRadio?.value || null;

  try {
    await api.createMeal({
      source_type: "photo",
      meal_label: label,
      created_at: dt ? new Date(dt).toISOString() : undefined,
      items,
    });
    showToast("✅ Pasto salvato!");
    state.analyzeResults = null;
    setTimeout(() => navigate("#diary"), 500);
  } catch (err) {
    showToast("❌ Errore: " + err.message);
  }
}

// --- Diary ---
async function loadDiary() {
  const container = $("view-diary");
  container.innerHTML = `
    <div class="view-header">
      <button class="btn-back" onclick="location.hash='#home'">←</button>
      <h2>Diario alimentare</h2>
    </div>
    <div class="date-nav">
      <button class="btn btn-small" id="prev-day">←</button>
      <input type="date" id="diary-date" value="${state.date}" />
      <button class="btn btn-small" id="next-day">→</button>
    </div>
    <div id="diary-summary"></div>
    <div id="diary-meals"></div>
    <button class="btn btn-outline" onclick="location.hash='#home'">+ Nuovo pasto</button>
  `;
  $("diary-date").onchange = () => { state.date = $("diary-date").value; loadDiaryData(); };
  $("prev-day").onclick = () => { const d = new Date(state.date); d.setDate(d.getDate() - 1); state.date = d.toISOString().slice(0, 10); $("diary-date").value = state.date; loadDiaryData(); };
  $("next-day").onclick = () => { const d = new Date(state.date); d.setDate(d.getDate() + 1); state.date = d.toISOString().slice(0, 10); $("diary-date").value = state.date; loadDiaryData(); };
  loadDiaryData();
}

async function loadDiaryData() {
  try {
    const summary = await api.dailySummary(state.date);
    state.dailyTotals = summary;
    renderDiarySummary(summary);
    renderDiaryMeals(summary.meals);
  } catch (err) {
    $("diary-meals").innerHTML = `<p class="error">Errore: ${err.message}</p>`;
  }
}

function renderDiarySummary(summary) {
  $("diary-summary").innerHTML = `
    <div class="totals-card">
      <div class="totals-row">
        <div class="total-item"><span class="total-value">${round(summary.total_kcal)}</span><span class="total-label">kcal</span></div>
        <div class="total-item"><span class="total-value">${round(summary.total_protein)}</span><span class="total-label">proteine</span></div>
        <div class="total-item"><span class="total-value">${round(summary.total_carbs)}</span><span class="total-label">carbs</span></div>
        <div class="total-item"><span class="total-value">${round(summary.total_fat)}</span><span class="total-label">grassi</span></div>
      </div>
    </div>`;
}

function labelName(v) {
  const found = LABELS.find(l => l.value === v);
  return found ? found.label : "";
}

function renderDiaryMeals(meals) {
  const el = $("diary-meals");
  if (!meals || meals.length === 0) {
    el.innerHTML = `<div class="empty-state"><p>Nessun pasto per questo giorno.</p></div>`;
    return;
  }
  el.innerHTML = meals.map(m => `
    <div class="meal-card" onclick="location.hash='#meal/${m.id}'">
      <div class="meal-header">
        <span class="meal-time">${formatTime(m.created_at)}</span>
        <span class="meal-source">${sourceIcon(m.source_type)} ${m.meal_label ? labelName(m.meal_label) : m.source_type}</span>
      </div>
      <div class="meal-items">
        ${m.items.map(i => `<span class="meal-item-name">${i.name} (${round(i.estimated_grams)}g)</span>`).join(", ")}
      </div>
      <div class="meal-totals"><span>🔥 ${round(m.items.reduce((a, i) => a + i.kcal, 0))} kcal</span></div>
    </div>`).join("");
}

// --- Meal Detail ---
async function loadMeal(id) {
  const container = $("view-meal");
  container.innerHTML = `<p class="loading">Caricamento...</p>`;
  try {
    const meal = await api.getMeal(id);
    const totalKcal = meal.items.reduce((a, i) => a + i.kcal, 0);
    container.innerHTML = `
      <div class="view-header">
        <button class="btn-back" onclick="location.hash='#diary'">←</button>
        <h2>Dettaglio pasto</h2>
      </div>
      <div class="meal-detail">
        <p class="meal-meta">
          ${formatTime(meal.created_at)} · ${sourceIcon(meal.source_type)} ${meal.meal_label ? labelName(meal.meal_label) : meal.source_type}
          ${meal.notes ? `<br/>📝 ${meal.notes}` : ""}
        </p>
        <h3>Alimenti</h3>
        <div id="detail-items">
          ${meal.items.map((i) => {
            const kcal100 = i.estimated_grams > 0 ? round(i.kcal / i.estimated_grams * 100) : 0;
            const p100 = i.estimated_grams > 0 ? round(i.protein_g / i.estimated_grams * 100) : 0;
            const c100 = i.estimated_grams > 0 ? round(i.carbs_g / i.estimated_grams * 100) : 0;
            const f100 = i.estimated_grams > 0 ? round(i.fat_g / i.estimated_grams * 100) : 0;
            return `
            <div class="item-card detail-item" data-item-id="${i.id}">
              <div class="detail-item-row">
                <input type="text" class="detail-name" value="${i.name}" />
                <input type="number" class="detail-grams" value="${round(i.estimated_grams)}" min="1"
                  data-kcal100="${kcal100}" data-p100="${p100}" data-c100="${c100}" data-f100="${f100}" />
                <span class="detail-unit">g</span>
              </div>
              <div class="detail-nutrients">
                <label>Kcal: <input type="number" class="detail-kcal" value="${round(i.kcal)}" step="0.1" /></label>
                <label>P: <input type="number" class="detail-protein" value="${round(i.protein_g)}" step="0.1" /></label>
                <label>C: <input type="number" class="detail-carbs" value="${round(i.carbs_g)}" step="0.1" /></label>
                <label>F: <input type="number" class="detail-fat" value="${round(i.fat_g)}" step="0.1" /></label>
              </div>
              <button class="btn btn-danger btn-sm remove-detail-item">Rimuovi</button>
            </div>`;}).join("")}
        </div>
        <div class="detail-total"><strong>Totale: ${round(totalKcal)} kcal</strong></div>
        <div class="meal-metadata mt-16">
          <label>Etichetta:</label>
          <div class="label-group">
            ${LABELS.map(l => `<label class="label-btn ${meal.meal_label === l.value ? 'active' : ''}"><input type="radio" name="detail-label" value="${l.value}" ${meal.meal_label === l.value ? 'checked' : ''} /> ${l.label}</label>`).join("")}
          </div>
        </div>
        <div class="detail-actions">
          <button class="btn btn-primary" id="save-meal-changes">Salva modifiche</button>
          <button class="btn btn-danger" id="delete-meal-btn">Elimina pasto</button>
        </div>
      </div>`;

    container.querySelectorAll(".detail-grams").forEach(el => el.oninput = recalcDetailNutrients);
    container.querySelectorAll(".remove-detail-item").forEach(btn => btn.onclick = () => btn.closest(".detail-item").remove());
    $("save-meal-changes").onclick = () => saveMealChanges(id);
    $("delete-meal-btn").onclick = () => deleteMeal(id);
  } catch (err) {
    container.innerHTML = `<p class="error">Errore: ${err.message}</p>`;
  }
}

function recalcDetailNutrients(e) {
  const card = e.target.closest(".detail-item");
  const grams = parseFloat(e.target.value) || 0;
  const factor = grams / 100;
  card.querySelector(".detail-kcal").value = round((parseFloat(e.target.dataset.kcal100) || 0) * factor);
  card.querySelector(".detail-protein").value = round((parseFloat(e.target.dataset.p100) || 0) * factor);
  card.querySelector(".detail-carbs").value = round((parseFloat(e.target.dataset.c100) || 0) * factor);
  card.querySelector(".detail-fat").value = round((parseFloat(e.target.dataset.f100) || 0) * factor);
}

function saveMealChanges(id) {
  const items = [];
  document.querySelectorAll(".detail-item").forEach(el => {
    items.push({
      name: el.querySelector(".detail-name").value,
      estimated_grams: parseFloat(el.querySelector(".detail-grams").value) || 100,
      kcal: parseFloat(el.querySelector(".detail-kcal").value) || 0,
      protein_g: parseFloat(el.querySelector(".detail-protein").value) || 0,
      carbs_g: parseFloat(el.querySelector(".detail-carbs").value) || 0,
      fat_g: parseFloat(el.querySelector(".detail-fat").value) || 0,
      source: "manual",
    });
  });
  const labelRadio = document.querySelector('input[name="detail-label"]:checked');
  const payload = { items };
  if (labelRadio) payload.meal_label = labelRadio.value;

  api.updateMeal(id, payload)
    .then(() => { showToast("✅ Modifiche salvate!"); loadMeal(id); })
    .catch(err => showToast("❌ " + err.message));
}

function deleteMeal(id) {
  if (!confirm("Eliminare questo pasto?")) return;
  api.deleteMeal(id)
    .then(() => { showToast("✅ Pasto eliminato"); setTimeout(() => navigate("#diary"), 500); })
    .catch(err => showToast("❌ " + err.message));
}
