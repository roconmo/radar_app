import re
from datetime import datetime
from dateutil import parser as dateparser
from app.models.schemas import RawArticle, NormalizedArticle


def normalize(articles: list[RawArticle]) -> list[NormalizedArticle]:
    result = []
    for a in articles:
        n = _normalize_one(a)
        if n is not None:
            result.append(n)
    return result


def _normalize_one(article: RawArticle) -> NormalizedArticle | None:
    url = article.url.strip()
    if not url.startswith("http"):
        return None  # descarta URLs relativas (sin dominio base)
    return NormalizedArticle(
        title=_clean_text(article.title),
        url=url,
        source=article.source.strip(),
        published_at=_parse_date(article.published_at),
        content=_clean_text(article.content or article.summary or ""),
    )


def _clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)          # strip HTML
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return dateparser.parse(raw)
    except Exception:
        return None
