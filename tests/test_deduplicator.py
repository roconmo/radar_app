from app.models.schemas import NormalizedArticle
from app.services.deduplicator import deduplicate


def _article(title: str, url: str) -> NormalizedArticle:
    return NormalizedArticle(title=title, url=url, source="test", content="")


def test_removes_duplicate_url():
    articles = [_article("Noticia A", "http://x.com/1"), _article("Noticia B", "http://x.com/1")]
    result = deduplicate(articles)
    assert len(result) == 1


def test_removes_similar_titles():
    articles = [
        _article("El mercado inmobiliario sube en Madrid", "http://x.com/1"),
        _article("El mercado inmobiliario sube en Madrid hoy", "http://x.com/2"),
    ]
    result = deduplicate(articles)
    assert len(result) == 1


def test_keeps_different_articles():
    articles = [
        _article("Inversión en energía solar", "http://x.com/1"),
        _article("Nuevo proyecto residencial en Barcelona", "http://x.com/2"),
    ]
    result = deduplicate(articles)
    assert len(result) == 2
