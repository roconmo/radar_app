from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RawArticle(BaseModel):
    """Lo que llega desde n8n (raw, sin normalizar)."""
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None


class NormalizedArticle(BaseModel):
    """Artículo tras normalización y deduplicación."""
    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    content: str
    is_new: bool = True  # False si ya estaba en histórico


class Insight(BaseModel):
    title: str
    summary: str
    relevance: str        # alta / media / baja
    sources: list[str]
    tags: list[str]


class ProcessResponse(BaseModel):
    """Respuesta que devuelve la API a n8n."""
    articles_received: int
    articles_after_dedup: int
    new_articles: int
    insights: list[Insight]
