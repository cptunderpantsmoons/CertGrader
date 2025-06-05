import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/backend/modal_grader")))
import modal_grader

class DummyModel:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
    def eval(self):
        pass
    def __call__(self, x):
        if self.should_fail:
            raise RuntimeError("Model inference failed")
        # Simulate output tensor for 3 classes
        import torch
        return torch.tensor([[0.1, 0.8, 0.1]])

@pytest.fixture
def patch_modal(monkeypatch):
    # Patch model loading and image processing
    monkeypatch.setattr(modal_grader, "load_model", lambda: DummyModel())
    monkeypatch.setattr(modal_grader, "preprocess_image", lambda img: "dummy_tensor")
    monkeypatch.setattr(modal_grader, "decode_base64_image", lambda b64: "dummy_image")
    monkeypatch.setattr(modal_grader, "GRADE_LABELS", ["Poor", "Mint 9", "Gem 10"])
    return modal_grader

def test_grade_card_success(patch_modal):
    # Patch model to not fail
    patch_modal.model = DummyModel()
    result = patch_modal.grade_card("dummy_b64")
    assert result["status"] == "success"
    assert result["grade"] == "Mint 9"
    assert 0.7 < result["confidence"] < 0.9

def test_grade_card_model_failure(monkeypatch):
    # Patch model to fail
    monkeypatch.setattr(modal_grader, "load_model", lambda: DummyModel(should_fail=True))
    monkeypatch.setattr(modal_grader, "preprocess_image", lambda img: "dummy_tensor")
    monkeypatch.setattr(modal_grader, "decode_base64_image", lambda b64: "dummy_image")
    monkeypatch.setattr(modal_grader, "GRADE_LABELS", ["Poor", "Mint 9", "Gem 10"])
    modal_grader.model = DummyModel(should_fail=True)
    result = modal_grader.grade_card("dummy_b64")
    assert result["status"] == "error"
    assert "Model inference failed" in result["error_message"]

def test_grade_card_invalid_base64(monkeypatch):
    # Patch decode to raise error
    def bad_decode(b64):
        raise ValueError("Invalid base64")
    monkeypatch.setattr(modal_grader, "decode_base64_image", bad_decode)
    monkeypatch.setattr(modal_grader, "load_model", lambda: DummyModel())
    monkeypatch.setattr(modal_grader, "preprocess_image", lambda img: "dummy_tensor")
    monkeypatch.setattr(modal_grader, "GRADE_LABELS", ["Poor", "Mint 9", "Gem 10"])
    modal_grader.model = DummyModel()
    result = modal_grader.grade_card("bad_b64")
    assert result["status"] == "error"
    assert "Invalid base64" in result["error_message"]