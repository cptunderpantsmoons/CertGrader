"""
Modal Labs AI Grading Stub for PokéCertify

This module defines a Modal Labs endpoint for grading card images.
For MVP, this is a stub that returns a fixed grade and confidence.
Replace with actual model inference for production.

Author: PokéCertify Team
"""

import base64
from io import BytesIO
from typing import List

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Image = None  # type: ignore

try:
    import torch  # type: ignore
    from torchvision import transforms, models  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    torch = None  # type: ignore
    transforms = None  # type: ignore
    models = None  # type: ignore

try:
    import modal  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    modal = None

# Modal setup using the new App API. This allows the backend to look up the
# deployed grading function. During unit tests this lookup will fail, but the
# resulting `grader` object will still be patchable.
try:  # pragma: no cover - network access may fail in tests
    app = modal.App.lookup("card-grader")
    grader = modal.Function.lookup("card-grader", "grade_card")
except Exception:  # Fallback for local testing
    class _LocalGrader:
        async def remote(self, *_args, **_kwargs):
            raise RuntimeError("Modal function not available")

    grader = _LocalGrader()


GRADE_LABELS: List[str] = ["Poor", "Mint 9", "Gem 10"]


def load_model():
    """Load the grading model (stub implementation)."""
    if models is None:
        raise RuntimeError("PyTorch not available")
    model = models.resnet18(weights=None)
    model.eval()
    return model


def decode_base64_image(b64: str) -> Image.Image:
    """Decode a base64 encoded image string."""
    try:
        header, data = b64.split(",", 1)
        return Image.open(BytesIO(base64.b64decode(data)))
    except Exception as exc:  # pragma: no cover - simple utility
        raise ValueError(str(exc)) from exc


def preprocess_image(img: Image.Image):
    """Preprocess PIL image for the model."""
    if transforms is None:
        raise RuntimeError("PyTorch not available")
    transform = transforms.Compose(
        [transforms.Resize((224, 224)), transforms.ToTensor()]
    )
    return transform(img).unsqueeze(0)


# Loaded model stored globally so tests can monkeypatch it
try:
    model = load_model()
except Exception:
    model = None


def grade_card(image_b64: str) -> dict:
    """Grade a card image and return the grade and confidence."""
    try:
        img = decode_base64_image(image_b64)
        tensor = preprocess_image(img)
        if model is None:
            raise RuntimeError("Model not available")
        # Handle missing torch gracefully
        if torch is not None:
            with torch.no_grad():
                output = model(tensor)
            idx = int(torch.argmax(output))
            confidence = float(output[0, idx].item())
        else:
            class _NoGrad:
                def __enter__(self):
                    return None
                def __exit__(self, *args):
                    return False
            with _NoGrad():
                output = model(tensor)
            idx = max(range(len(output[0])), key=lambda i: output[0][i])
            confidence = float(output[0][idx])
        return {
            "status": "success",
            "grade": GRADE_LABELS[idx % len(GRADE_LABELS)],
            "confidence": confidence,
        }
    except Exception as exc:
        return {"status": "error", "error_message": str(exc)}


__all__ = ["grade_card", "grader", "load_model", "preprocess_image", "decode_base64_image", "GRADE_LABELS", "model"]
