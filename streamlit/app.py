import streamlit as st
import datetime
from datetime import timezone
import cv2
import numpy as np
from PIL import Image

from db.database import init_db, SessionLocal
from db.models import Meal, MealItem
from services.barcode_service import lookup_barcode
from services.nutrition_service import get_nutrition_for_food, compute_nutrients, search_foods
from ml.food_classifier import classify_food_image
from ml.portion_estimator import estimate_portion

st.set_page_config(page_title="Meal Tracker", page_icon="🍽️", layout="centered")

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

if "pending_items" not in st.session_state:
    st.session_state.pending_items = []

if "editor_version" not in st.session_state:
    st.session_state.editor_version = 0

if "barcode_result" not in st.session_state:
    st.session_state.barcode_result = None

if "readd_items" not in st.session_state:
    st.session_state.readd_items = []

db = SessionLocal()

LABELS = {
    "breakfast": "Colazione",
    "snack": "Snack",
    "lunch": "Pranzo",
    "dinner": "Cena",
}

st.title("🍽️ Meal Tracker")

menu = st.sidebar.radio(
    "Navigazione",
    ["📓 Diario", "📷 Analizza Foto", "📱 Scansiona Barcode"],
    label_visibility="collapsed",
)


def save_meal(source_type, items, meal_label=None, notes=None):
    meal = Meal(
        source_type=source_type,
        meal_label=meal_label,
        notes=notes,
        created_at=datetime.datetime.now(timezone.utc),
    )
    db.add(meal)
    db.flush()
    for item in items:
        db.add(MealItem(
            meal_id=meal.id,
            name=item["name"],
            source=item.get("source", "manual"),
            confidence=item.get("confidence"),
            estimated_grams=item["estimated_grams"],
            kcal=item["kcal"],
            protein_g=item["protein_g"],
            carbs_g=item["carbs_g"],
            fat_g=item["fat_g"],
            barcode=item.get("barcode"),
            external_product_id=item.get("external_product_id"),
        ))
    db.commit()
    return meal


def format_label(v):
    return LABELS.get(v, v or "")


def handle_editor_change():
    editor_key = f"photo_editor_{st.session_state.editor_version}"
    state = st.session_state.get(editor_key, {})
    if not state:
        return

    has_changes = False

    # 1. Handle deleted rows
    deleted_rows = state.get("deleted_rows", [])
    if deleted_rows:
        for index in sorted(deleted_rows, reverse=True):
            if 0 <= index < len(st.session_state.pending_items):
                st.session_state.pending_items.pop(index)
        has_changes = True

    # 2. Handle added rows
    added_rows = state.get("added_rows", [])
    for added in added_rows:
        new_item = {
            "name": added.get("name") or "Nuovo alimento",
            "source": added.get("source") or "manual",
            "confidence": added.get("confidence") or 0.0,
            "estimated_grams": added.get("estimated_grams") or 100.0,
            "kcal": added.get("kcal") or 0.0,
            "protein_g": added.get("protein_g") or 0.0,
            "carbs_g": added.get("carbs_g") or 0.0,
            "fat_g": added.get("fat_g") or 0.0,
        }
        grams = new_item["estimated_grams"]
        nutrients = compute_nutrients(new_item["name"], grams)
        new_item.update(nutrients)
        st.session_state.pending_items.append(new_item)
        has_changes = True

    # 3. Handle edited rows
    edited_rows = state.get("edited_rows", {})
    for index_str, changes in edited_rows.items():
        index = int(index_str)
        if 0 <= index < len(st.session_state.pending_items):
            item = st.session_state.pending_items[index]
            
            name_changed = "name" in changes
            grams_changed = "estimated_grams" in changes
            
            # Apply individual changes
            for col, val in changes.items():
                item[col] = val
                
            # If name or grams changed, recompute nutrients
            if name_changed or grams_changed:
                nutrients = compute_nutrients(item["name"], item["estimated_grams"])
                item.update(nutrients)
            has_changes = True

    if has_changes:
        st.session_state.editor_version += 1


# ==========================================
# DIARIO
# ==========================================
if menu == "📓 Diario":
    st.subheader("Diario Alimentare")

    target_date = st.date_input("Giorno", datetime.date.today(), label_visibility="collapsed")

    start_dt = datetime.datetime.combine(target_date, datetime.time.min, tzinfo=timezone.utc)
    end_dt = datetime.datetime.combine(target_date, datetime.time.max, tzinfo=timezone.utc)

    meals = db.query(Meal).filter(
        Meal.created_at >= start_dt,
        Meal.created_at <= end_dt,
    ).order_by(Meal.created_at.asc()).all()

    tot_kcal = sum(i.kcal for m in meals for i in m.items)
    tot_prot = sum(i.protein_g for m in meals for i in m.items)
    tot_carbs = sum(i.carbs_g for m in meals for i in m.items)
    tot_fat = sum(i.fat_g for m in meals for i in m.items)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kcal", f"{round(tot_kcal, 1)}")
    c2.metric("Proteine", f"{round(tot_prot, 1)}g")
    c3.metric("Carbs", f"{round(tot_carbs, 1)}g")
    c4.metric("Grassi", f"{round(tot_fat, 1)}g")

    st.divider()

    if not meals:
        st.info("Nessun pasto registrato per questo giorno.")
    else:
        for meal in meals:
            meal_kcal = sum(i.kcal for i in meal.items)
            label_str = f" · {format_label(meal.meal_label)}" if meal.meal_label else ""
            icon = "📷" if meal.source_type == "photo" else "📱" if meal.source_type == "barcode" else "✏️"

            with st.expander(f"{icon} {meal.created_at.strftime('%H:%M')}{label_str} — {round(meal_kcal)} kcal"):
                for item in meal.items:
                    col_info, col_btn = st.columns([5, 1])
                    with col_info:
                        st.write(
                            f"**{item.name}** ({round(item.estimated_grams)}g) — "
                            f"{round(item.kcal)} kcal · P {round(item.protein_g)}g · "
                            f"C {round(item.carbs_g)}g · F {round(item.fat_g)}g"
                        )
                    with col_btn:
                        if st.button("🔄", key=f"readd_{meal.id}_{item.id}", help="Riaggiungi alimento"):
                            st.session_state.readd_items.append({
                                "name": item.name,
                                "source": "re-added",
                                "confidence": 0,
                                "estimated_grams": item.estimated_grams,
                                "kcal": item.kcal,
                                "protein_g": item.protein_g,
                                "carbs_g": item.carbs_g,
                                "fat_g": item.fat_g,
                            })
                            st.rerun()
                if meal.notes:
                    st.caption(f"📝 {meal.notes}")

                if st.button("🗑️ Elimina", key=f"del_{meal.id}", type="secondary"):
                    db.delete(meal)
                    db.commit()
                    st.rerun()


# ==========================================
# ANALIZZA FOTO
# ==========================================
elif menu == "📷 Analizza Foto":
    st.subheader("Analizza Foto")

    if st.session_state.readd_items:
        st.session_state.pending_items.extend(st.session_state.readd_items)
        st.session_state.readd_items = []
        st.rerun()

    img_file = st.camera_input("Scatta una foto del pasto")
    if not img_file:
        img_file = st.file_uploader("Oppure carica un'immagine", type=["jpg", "jpeg", "png"])

    if img_file:
        image = Image.open(img_file)
        st.image(image, caption="Anteprima", use_container_width=True)

        if st.button("🔍 Analizza Alimenti", type="primary"):
            with st.spinner("Classificazione in corso..."):
                img_bytes = img_file.getvalue()
                classifications = classify_food_image(img_bytes)

                st.session_state.pending_items = []
                for food_name, confidence in classifications:
                    grams = estimate_portion(food_name, img_bytes)
                    nutrients = compute_nutrients(food_name, grams)
                    st.session_state.pending_items.append({
                        "name": nutrients["name"],
                        "source": "classification",
                        "confidence": round(confidence, 3),
                        "estimated_grams": grams,
                        "kcal": nutrients["kcal"],
                        "protein_g": nutrients["protein_g"],
                        "carbs_g": nutrients["carbs_g"],
                        "fat_g": nutrients["fat_g"],
                    })

                if not classifications:
                    st.warning("Nessun alimento riconosciuto. Aggiungilo manualmente nella tabella qui sotto.")
                    st.session_state.pending_items.append({
                        "name": "Nuovo alimento",
                        "source": "manual",
                        "confidence": 0,
                        "estimated_grams": 100,
                        "kcal": 0,
                        "protein_g": 0,
                        "carbs_g": 0,
                        "fat_g": 0,
                    })

        if st.session_state.pending_items:
            st.markdown("### Rivedi e modifica")
            st.caption("Modifica i campi direttamente nella tabella. Cambiando alimento o grammature i valori nutrizionali si ricalcolano automaticamente.")

            with st.expander("➕ Aggiungi alimento personalizzato (non dal database)"):
                custom_cols = st.columns([2, 1, 1, 1, 1, 1])
                custom_name = custom_cols[0].text_input("Nome alimento", key="custom_food_name")
                custom_grams = custom_cols[1].number_input("Grammi", min_value=1, value=100, step=1, key="custom_food_grams")
                custom_kcal = custom_cols[2].number_input("Kcal/100g", min_value=0.0, value=0.0, step=0.1, key="custom_food_kcal")
                custom_prot = custom_cols[3].number_input("Prot/100g", min_value=0.0, value=0.0, step=0.1, key="custom_food_prot")
                custom_carbs = custom_cols[4].number_input("Carb/100g", min_value=0.0, value=0.0, step=0.1, key="custom_food_carbs")
                custom_fat = custom_cols[5].number_input("Grassi/100g", min_value=0.0, value=0.0, step=0.1, key="custom_food_fat")
                if st.button("➕ Aggiungi alla tabella", key="add_custom_food"):
                    if custom_name.strip():
                        factor = custom_grams / 100.0
                        st.session_state.pending_items.append({
                            "name": custom_name.strip(),
                            "source": "manual",
                            "confidence": 0,
                            "estimated_grams": custom_grams,
                            "kcal": round(custom_kcal * factor, 1),
                            "protein_g": round(custom_prot * factor, 1),
                            "carbs_g": round(custom_carbs * factor, 1),
                            "fat_g": round(custom_fat * factor, 1),
                        })
                        st.session_state.editor_version += 1
                        st.rerun()
                    else:
                        st.warning("Inserisci il nome dell'alimento.")

            food_options = sorted({f["name"] for f in search_foods("", limit=1000)})

            editor_key = f"photo_editor_{st.session_state.editor_version}"

            edited_items = st.data_editor(
                st.session_state.pending_items,
                num_rows="dynamic",
                key=editor_key,
                on_change=handle_editor_change,
                column_config={
                    "name": st.column_config.SelectboxColumn("Alimento", options=food_options, width="medium"),
                    "source": st.column_config.TextColumn("Fonte", width="small"),
                    "confidence": st.column_config.NumberColumn("Confidenza", format="%.2f", width="small"),
                    "estimated_grams": st.column_config.NumberColumn("Grammi", min_value=1, step=1),
                    "kcal": st.column_config.NumberColumn("Kcal", min_value=0, step=0.1),
                    "protein_g": st.column_config.NumberColumn("Proteine (g)", min_value=0, step=0.1),
                    "carbs_g": st.column_config.NumberColumn("Carbs (g)", min_value=0, step=0.1),
                    "fat_g": st.column_config.NumberColumn("Grassi (g)", min_value=0, step=0.1),
                },
                hide_index=True,
            )

            col1, col2 = st.columns(2)
            meal_label = col1.selectbox("Tipo pasto", ["colazione", "snack", "pranzo", "cena"])
            notes = col2.text_input("Note (opzionale)")

            if st.button("💾 Salva pasto", type="primary"):
                save_meal("photo", edited_items, meal_label=meal_label, notes=notes)
                st.success("✅ Pasto salvato!")
                st.session_state.pending_items = []
                st.rerun()


# ==========================================
# SCANSIONA BARCODE
# ==========================================
elif menu == "📱 Scansiona Barcode":
    st.subheader("Scanner Barcode")

    barcode_img = st.camera_input("Inquadra il codice a barre e scatta")
    manual_barcode = st.text_input("Oppure inserisci il codice manualmente:")

    barcode_to_search = None
    if manual_barcode:
        barcode_to_search = manual_barcode.strip()
    elif barcode_img:
        file_bytes = np.asarray(bytearray(barcode_img.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # 1. Prova con OpenCV BarcodeDetector sull'immagine originale
        detector = cv2.barcode.BarcodeDetector()
        retval, decoded_info, decoded_type, points = detector.detectAndDecode(img)

        # 2. Se fallisce, prova con preprocessing (grayscale + Otsu threshold)
        if not retval:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            retval, decoded_info, decoded_type, points = detector.detectAndDecode(thresh)

        # 3. CLAHE (contrasto locale migliorato)
        if not retval:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            retval, decoded_info, decoded_type, points = detector.detectAndDecode(enhanced)

        # 4. Blur + threshold adattivo
        if not retval:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            retval, decoded_info, decoded_type, points = detector.detectAndDecode(adaptive)

        # 5. Prova su immagini ruotate (90, 180, 270 gradi)
        if not retval:
            for angle in [90, 180, 270]:
                h, w = img.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR)
                retval, decoded_info, decoded_type, points = detector.detectAndDecode(rotated)
                if retval:
                    break

        if not retval and barcode_to_search is None:
            barcode_to_search = decoded_info[0] if retval else None

        if barcode_to_search:
            st.success(f"Codice rilevato: **{barcode_to_search}**")
        else:
            st.warning("Barcode non leggibile. Riprova con più luce o digita il codice.")

    if barcode_to_search:
        product = lookup_barcode(barcode_to_search, db)

        if product and product.get("found"):
            st.success(f"**{product['name']}**")
            if product.get("brand"):
                st.caption(f"Marca: {product['brand']}")

            n100 = product["nutriments_per_100g"]
            st.markdown(
                f"**Per 100g:** 🔥 {n100.get('energy_kcal', 0)} kcal · "
                f"🥩 P {n100.get('protein', 0)}g · "
                f"🍚 C {n100.get('carbohydrates', 0)}g · "
                f"🧈 F {n100.get('fat', 0)}g"
            )

            if product.get("ingredients_text"):
                with st.expander("Ingredienti"):
                    st.write(product["ingredients_text"])

            grams = st.number_input("Quantità consumata (g)", min_value=1, value=100, step=1)
            factor = grams / 100.0

            kcal_calc = round((n100.get("energy_kcal") or 0) * factor, 1)
            p_calc = round((n100.get("protein") or 0) * factor, 1)
            c_calc = round((n100.get("carbohydrates") or 0) * factor, 1)
            f_calc = round((n100.get("fat") or 0) * factor, 1)

            st.markdown(
                f"**Porzione ({round(grams)}g):** 🔥 **{kcal_calc}** kcal · "
                f"🥩 **{p_calc}**g · 🍚 **{c_calc}**g · 🧈 **{f_calc}**g"
            )

            col1, col2 = st.columns(2)
            meal_label = col1.selectbox("Tipo pasto", ["colazione", "snack", "pranzo", "cena"], key="bc_label")
            notes = col2.text_input("Note (opzionale)", key="bc_notes")

            if st.button("💾 Salva pasto", type="primary"):
                save_meal("barcode", [{
                    "name": product["name"],
                    "source": "barcode",
                    "estimated_grams": grams,
                    "kcal": kcal_calc,
                    "protein_g": p_calc,
                    "carbs_g": c_calc,
                    "fat_g": f_calc,
                    "barcode": barcode_to_search,
                    "external_product_id": barcode_to_search,
                }], meal_label=meal_label, notes=notes)
                st.success("✅ Pasto salvato!")
                st.balloons()
                st.session_state.barcode_result = None
                st.rerun()
        else:
            st.error("❌ Prodotto non trovato su Open Food Facts.")
            st.info("Puoi inserire i dati manualmente nella sezione 'Analizza Foto'.")
