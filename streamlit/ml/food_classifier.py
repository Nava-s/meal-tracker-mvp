import io

from PIL import Image as PILImage

MODEL_NAME = "nateraw/food"

_model_pipeline = None


def _load_model():
    global _model_pipeline
    if _model_pipeline is not None:
        return _model_pipeline
    try:
        from transformers import pipeline
        _model_pipeline = pipeline("image-classification", model=MODEL_NAME)
    except Exception as e:
        print(f"[WARN] Could not load food classifier model: {e}")
        print("[WARN] Using fallback heuristic classification")
        _model_pipeline = None
    return _model_pipeline


def classify_food_image(image_bytes: bytes, top_k: int = 3) -> list[tuple[str, float]]:
    pipeline = _load_model()
    if pipeline is None:
        return _fallback_classify(image_bytes)

    try:
        image = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        results = pipeline(image, top_k=top_k)
        return [(r["label"], r["score"]) for r in results]
    except Exception as e:
        print(f"[WARN] Classification error: {e}")
        return _fallback_classify(image_bytes)


def _fallback_classify(image_bytes: bytes) -> list[tuple[str, float]]:
    return []
