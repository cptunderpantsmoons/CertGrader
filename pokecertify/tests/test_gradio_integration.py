import pytest
import subprocess
import time
import requests

# These tests assume the Gradio app is running locally on port 7860 and the backend API is available.
# For a true integration test, use Selenium or Playwright for UI interaction.
# Here, we test the backend endpoints as used by the Gradio frontend.

API_URL = "http://localhost:8000"

def test_upload_and_verify_card(tmp_path):
    # Simulate image upload as Gradio would do
    test_image_path = tmp_path / "test_card.jpg"
    # Create a dummy image file
    from PIL import Image
    img = Image.new("RGB", (100, 100), color="red")
    img.save(test_image_path)
    with open(test_image_path, "rb") as img_file:
        response = requests.post(
            f"{API_URL}/upload",
            files={"file": ("test_card.jpg", img_file, "image/jpeg")},
            data={"card_name": "TestCard", "card_info": "Integration", "owner": "integration_user"}
        )
    assert response.status_code == 200
    data = response.json()
    card_id = data["card_id"]
    assert data["card_name"] == "TestCard"
    assert data["owner"] == "integration_user"

    # Verify card
    response = requests.get(f"{API_URL}/card/{card_id}")
    assert response.status_code == 200
    card = response.json()
    assert card["card_name"] == "TestCard"
    assert card["owner"] == "integration_user"

def test_trade_card_integration(tmp_path):
    # Upload a card first
    from PIL import Image
    test_image_path = tmp_path / "test_card2.jpg"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(test_image_path)
    with open(test_image_path, "rb") as img_file:
        response = requests.post(
            f"{API_URL}/upload",
            files={"file": ("test_card2.jpg", img_file, "image/jpeg")},
            data={"card_name": "TradeCard", "card_info": "Integration", "owner": "userA"}
        )
    assert response.status_code == 200
    card_id = response.json()["card_id"]

    # Trade the card
    response = requests.post(f"{API_URL}/trade", data={"card_id": card_id, "to_owner": "userB"})
    assert response.status_code == 200
    trade = response.json()
    assert trade["to_owner"] == "userB"

def test_collection_integration(tmp_path):
    # Upload two cards for the same owner
    from PIL import Image
    test_image_path1 = tmp_path / "test_card3.jpg"
    test_image_path2 = tmp_path / "test_card4.jpg"
    img1 = Image.new("RGB", (100, 100), color="green")
    img2 = Image.new("RGB", (100, 100), color="yellow")
    img1.save(test_image_path1)
    img2.save(test_image_path2)
    for img_path, name in [(test_image_path1, "ColCard1"), (test_image_path2, "ColCard2")]:
        with open(img_path, "rb") as img_file:
            response = requests.post(
                f"{API_URL}/upload",
                files={"file": (img_path.name, img_file, "image/jpeg")},
                data={"card_name": name, "card_info": "Integration", "owner": "collector"}
            )
            assert response.status_code == 200

    # Get collection
    response = requests.get(f"{API_URL}/collection/collector")
    assert response.status_code == 200
    collection = response.json()
    names = {c["card_name"] for c in collection}
    assert "ColCard1" in names and "ColCard2" in names