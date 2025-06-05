import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

# Ensure import path includes backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/backend/api")))
from src.backend.api.main import app, get_db_connection

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown_db(monkeypatch):
    # Use a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setenv("POKECERTIFY_DB_PATH", db_path)
    # Re-initialize DB schema
    conn = get_db_connection()
    with open(os.path.join(os.path.dirname(__file__), "../src/backend/db/schema.sql")) as f:
        conn.executescript(f.read())
    conn.close()
    yield
    os.close(db_fd)
    os.remove(db_path)

def test_upload_and_get_card(monkeypatch):
    # Mock Modal grader
    async def fake_grade_card(image_b64):
        return {"status": "success", "grade": "Mint 9", "confidence": 0.98}
    monkeypatch.setattr("src.backend.api.main.grader.remote", fake_grade_card)

    # Upload a card
    with open(os.path.join(os.path.dirname(__file__), "test_card.jpg"), "rb") as img:
        response = client.post(
            "/upload",
            files={"file": ("test_card.jpg", img, "image/jpeg")},
            data={"card_name": "Charizard", "card_info": "1st Edition", "owner": "ash"}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["grade"] == "Mint 9"
    card_id = data["card_id"]

    # Get card by ID
    response = client.get(f"/card/{card_id}")
    assert response.status_code == 200
    card = response.json()
    assert card["card_name"] == "Charizard"
    assert card["owner"] == "ash"

def test_trade_card(monkeypatch):
    # Mock Modal grader
    async def fake_grade_card(image_b64):
        return {"status": "success", "grade": "Mint 9", "confidence": 0.98}
    monkeypatch.setattr("src.backend.api.main.grader.remote", fake_grade_card)

    # Upload a card
    with open(os.path.join(os.path.dirname(__file__), "test_card.jpg"), "rb") as img:
        response = client.post(
            "/upload",
            files={"file": ("test_card.jpg", img, "image/jpeg")},
            data={"card_name": "Blastoise", "card_info": "Shadowless", "owner": "misty"}
        )
    card_id = response.json()["card_id"]

    # Trade card
    response = client.post("/trade", data={"card_id": card_id, "to_owner": "brock"})
    assert response.status_code == 200
    trade = response.json()
    assert trade["to_owner"] == "brock"

def test_get_collection(monkeypatch):
    # Mock Modal grader
    async def fake_grade_card(image_b64):
        return {"status": "success", "grade": "Mint 9", "confidence": 0.98}
    monkeypatch.setattr("src.backend.api.main.grader.remote", fake_grade_card)

    # Upload two cards for same owner
    with open(os.path.join(os.path.dirname(__file__), "test_card.jpg"), "rb") as img:
        client.post(
            "/upload",
            files={"file": ("test_card.jpg", img, "image/jpeg")},
            data={"card_name": "Pikachu", "card_info": "Promo", "owner": "ash"}
        )
    with open(os.path.join(os.path.dirname(__file__), "test_card.jpg"), "rb") as img:
        client.post(
            "/upload",
            files={"file": ("test_card.jpg", img, "image/jpeg")},
            data={"card_name": "Bulbasaur", "card_info": "Base", "owner": "ash"}
        )
    # Get collection
    response = client.get("/collection/ash")
    assert response.status_code == 200
    collection = response.json()
    assert len(collection) == 2
    names = {c["card_name"] for c in collection}
    assert "Pikachu" in names and "Bulbasaur" in names