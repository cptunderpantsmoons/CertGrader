import os
import io
import tempfile
from fastapi.testclient import TestClient
from PIL import Image
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # use a temporary database
    db_path = tmp_path / "test.db"
    os.environ["POKECERTIFY_DB_PATH"] = str(db_path)
    from src.backend.db import utils as db_utils
    db_utils.DB_PATH = str(db_path)
    db_utils.initialize_database()

    from src.backend.api.main import app

    class DummyGrader:
        async def remote(self, *_args, **_kwargs):
            return {"status": "success", "grade": "A", "confidence": 0.99}

    monkeypatch.setattr("src.backend.api.main.grader", DummyGrader())
    return TestClient(app)


def _create_image_bytes():
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_full_flow(client):
    img_buf = _create_image_bytes()
    response = client.post(
        "/upload",
        files={"file": ("card.png", img_buf, "image/png")},
        data={"card_name": "Test", "card_info": "info", "owner": "Ash"},
    )
    assert response.status_code == 200
    card_id = response.json()["card_id"]

    response = client.get(f"/card/{card_id}")
    assert response.status_code == 200
    assert response.json()["owner"] == "Ash"

    response = client.post("/trade", json={"card_id": card_id, "to_owner": "Brock"})
    assert response.status_code == 200
    assert response.json()["to_owner"] == "Brock"

    response = client.get("/collection/Brock")
    assert response.status_code == 200
    cards = response.json()
    assert any(c["card_id"] == card_id for c in cards)
