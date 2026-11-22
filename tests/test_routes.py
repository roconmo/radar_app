import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test")

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import insights


def test_process_returns_new_articles_list(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "history_db_path", str(tmp_path / "history.db"))
    monkeypatch.setattr(insights, "generate_insights", lambda articles: (None, "", []))
    monkeypatch.setattr(insights, "MAX_ARTICLES", 1)
    payload = {"articles": [
        {"title": "Roca presenta nueva colección", "url": "https://a.com/1", "source": "salabano",
         "published_at": "2026-10-01T08:00:00Z"},
        {"title": "Cosentino abre fábrica en Almería", "url": "https://a.com/2", "source": "cosentino"},
    ]}

    client = TestClient(app)
    first = client.post("/api/v1/process", json=payload).json()
    second = client.post("/api/v1/process", json=payload).json()

    arts = first["new_articles_list"]
    assert [a["url"] for a in arts] == ["https://a.com/1", "https://a.com/2"]
    assert arts[0]["source"] == "salabano" and arts[0]["published_at"].startswith("2026-10-01")
    assert [a["analizada"] for a in arts] == [True, False]
    assert second["new_articles_list"] == []
    assert first["empresa"] == "laguardia" and first["analysis_gabriela"] is None


def test_process_gabriela_uses_her_report(tmp_path, monkeypatch):
    from app.models.schemas import GabrielaAnalysis
    monkeypatch.setattr(settings, "history_db_path", str(tmp_path / "history.db"))

    def no_laguardia(articles):
        raise AssertionError("no debe usar el informe de Laguardia")

    monkeypatch.setattr(insights, "generate_insights", no_laguardia)
    monkeypatch.setattr(insights, "generate_gabriela",
                        lambda articles: (GabrielaAnalysis(resumen="ok"), "blob"))
    payload = {"empresa": "Gabriela Tassile", "articles": [
        {"title": "Congreso de Medicina Interna", "url": "https://b.com/1", "source": "mcb_calendario"},
    ]}

    data = TestClient(app).post("/api/v1/process", json=payload).json()

    assert data["empresa"] == "gabriela_tassile"
    assert data["analysis"] is None
    assert data["analysis_gabriela"]["resumen"] == "ok"
    assert data["raw_news_blob"] == "blob"


def test_process_rejects_unknown_company(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "history_db_path", str(tmp_path / "history.db"))
    payload = {"empresa": "otra", "articles": [{"title": "t", "url": "https://c.com", "source": "s"}]}
    assert TestClient(app).post("/api/v1/process", json=payload).status_code == 400
