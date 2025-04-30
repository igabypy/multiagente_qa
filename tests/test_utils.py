# multi_agent/tests/test_utils.py
import sys
from pathlib import Path
import json
import pytest

# inserta la carpeta padre (multi_agent/) en PYTHONPATH
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from app.multi_agent import classify_node, domain_node, router, classifier_chain, domain_chains

class DummyChain:
    """Stub chain that returns a fixed response."""
    def __init__(self, response):
        self.response = response

    def run(self, **kwargs):
        return self.response

def test_classify_node_maps_id_and_label(monkeypatch):
    """Verifica que classify_node extraiga category_id y category_label correctamente."""
    fake_raw = json.dumps({"id": 3})
    # parcheamos classifier_chain.run para no llamar al LLM real
    monkeypatch.setattr(classifier_chain, "run", lambda **kw: fake_raw)
    state = {"question": "¿X?", "category_id": None, "category_label": "", "answer": ""}
    new = classify_node(state.copy())
    assert new["category_id"] == 3
    # label por defecto para id=3 es "Médica"
    assert new["category_label"] == "Médica"

@pytest.mark.parametrize("cat_id,expected", [
    (1, "legal"),
    (2, "accounting"),
    (3, "medical"),
    (42, "generic"),
])
def test_router_returns_correct_node(cat_id, expected):
    """Comprueba que router() enrute según category_id."""
    state = {"question": "", "category_id": cat_id, "category_label": "", "answer": ""}
    assert router(state) == expected

def test_domain_node_sets_answer():
    """Verifica que domain_node() inserte la respuesta devuelta por el chain."""
    dummy = DummyChain("fake answer")
    node = domain_node(dummy)
    state = {"question": "hola", "category_id": 4, "category_label": "", "answer": ""}
    out = node(state.copy())
    assert out["answer"] == "fake answer"
