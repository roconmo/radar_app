from app.models.schemas import RawArticle
from app.services.normalizer import normalize


def test_strips_html():
    articles = [RawArticle(title="<b>Hola</b> mundo", url="http://x.com", source="test")]
    result = normalize(articles)
    assert result[0].title == "Hola mundo"


def test_parses_date():
    articles = [RawArticle(title="Test", url="http://x.com", source="test", published_at="2024-01-15")]
    result = normalize(articles)
    assert result[0].published_at is not None
    assert result[0].published_at.year == 2024


def test_handles_missing_content():
    articles = [RawArticle(title="Test", url="http://x.com", source="test", summary="resumen")]
    result = normalize(articles)
    assert result[0].content == "resumen"
