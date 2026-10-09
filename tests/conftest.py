import pytest

from app import classifier
from app.config import DATA_PATH, MODEL_PATH


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    """Make sure a dataset and model exist before any test runs."""
    from scripts.generate_data import generate
    if not DATA_PATH.exists():
        generate(DATA_PATH)
    if not MODEL_PATH.exists():
        classifier.train(verbose=False)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test gets its own empty database; LLM is disabled."""
    monkeypatch.setenv("TICKET_DB", str(tmp_path / "test.db"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
