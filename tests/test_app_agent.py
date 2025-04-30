# multi_agent/tests/test_app_agent.py
import sys
from pathlib import Path
import pytest

from fastapi.testclient import TestClient

# inserta la carpeta padre (multi_agent/) en PYTHONPATH
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from app.main_multi_agent import api
import app.main_multi_agent as main_mod

@pytest.fixture(autouse=True)
def patch_agent(monkeypatch):
    """Antes de cada test, parchea app_agent.invoke para respuestas predecibles."""
    dummy_response = {
        "category_id": 4,
        "category_label": "Genérica",
        "answer": "Respuesta simulada"
    }
    monkeypatch.setattr(main_mod, "app_agent", type("A", (), {"invoke": lambda self, x: dummy_response})())

def test_api_qa_success():
    """Testea el endpoint /qa con payload válido."""
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "¿Algo?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["category_id"] == 4
    assert data["category_label"] == "Genérica"
    assert data["answer"] == "Respuesta simulada"

def test_api_qa_empty_question():
    """Testea que /qa rechace preguntas vacías con 400."""
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "   "})
    assert resp.status_code == 400
    assert "Empty question" in resp.json()["detail"]
