import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/backend/api")))
from src.backend.api.main import app, get_db_connection

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown_db(monkeypatch):
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setenv("POKECERTIFY_DB_PATH", db_path)
    conn = get_db_connection()
    with open(os.path.join(os.path.dirname(__file__), "../src/backend/db/schema.sql")) as f:
        conn.executescript(f.read())
    conn.close()
    yield
    os.close(db_fd)
    os.remove(db_path)

def test_upload_missing_fields(monkeypatch):
    async def fake_grade_card(image_b64):
        return {"status": "success", "grade": "Mint 9", "confidence": 0.98}
    monkeypatch.setattr("src.backend.api.main.grader.remote", fake_grade_card)

    # Missing card_name
    with open(os.path.join(os.path.dirname(__file__), "test_card.jpg"), "rb") as img:
        response = client.post(
            "/upload",
            files={"file": ("test_card.jpg", img, "image/jpeg")},
            data={"card_info": "1st Edition", "owner": "ash"}
        )
    assert response.status_code == 400
    assert "Missing required fields" in response.text

def test_upload_invalid_file_type(monkeypatch):
    async def fake_grade_card(image_b64):
        return {"status": "success", "grade": "Mint 9", "confidence": 0.98}
    monkeypatch.setattr("src.backend.api.main.grader.remote", fake_grade_card)

    # Upload a text file instead of image
    response = client.post(
        "/upload",
        files={"file": ("not_an_image.txt", b"not an image", "text/plain")},
        data={"card_name": "Charizard", "card_info": "1st Edition", "owner": "ash"}
    )
    assert response.status_code == 400
    assert "File must be an image" in response.text

def test_get_card_not_found():
    response = client.get("/card/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "Card not found" in response.text

def test_trade_card_not_found():
    response = client.post("/trade", data={"card_id": "00000000-0000-0000-0000-000000000000", "to_owner": "brock"})
    assert response.status_code == 404
    assert "Card not found" in response.text

def test_trade_card_missing_to_owner(monkeypatch):
    async def fake_grade_card(image_b64):
        return {"status": "success", "grade": "Mint 9", "confidence": 0.98}
    monkeypatch.setattr("src.backend.api.main.grader.remote", fake_grade_card)

    # Upload a card
    with open(os.path.join(os.path.dirname(__file__), "test_card.jpg"), "rb") as img:
        response = client.post(
            "/upload",
            files={"file": ("test_card.jpg", img, "image/jpeg")},
            data={"card_name": "Squirtle", "card_info": "Base", "owner": "misty"}
        )
    card_id = response.json()["card_id"]

    # Trade with missing to_owner
    response = client.post("/trade", data={"card_id": card_id})
    assert response.status_code == 400
    assert "Missing to_owner" in response.text