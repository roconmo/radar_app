from difflib import SequenceMatcher
from app.models.schemas import NormalizedArticle
from app.core.config import settings


def deduplicate(articles: list[NormalizedArticle]) -> list[NormalizedArticle]:
    seen: list[NormalizedArticle] = []
    for article in articles:
        if not _is_duplicate(article, seen):
            seen.append(article)
    return seen


def _is_duplicate(candidate: NormalizedArticle, seen: list[NormalizedArticle]) -> bool:
    for existing in seen:
        if existing.url == candidate.url:
            return True
        if _similarity(candidate.title, existing.title) >= settings.similarity_threshold:
            return True
    return False


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
