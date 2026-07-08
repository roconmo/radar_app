from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RawArticle(BaseModel):
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None


class NormalizedArticle(BaseModel):
    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    content: str
    is_new: bool = True


class Insight(BaseModel):
    """Para el dashboard Streamlit (histórico visual)."""
    title: str
    summary: str
    relevance: str  # alta / media / baja
    sources: list[str]
    tags: list[str]


class LaguardiaAnalysis(BaseModel):
    """Schema de salida hacia Google Sheets (mismo formato que el workflow original)."""
    senales_relevantes: str
    early_signals: str
    market_shifts: str
    implicaciones: str
    oportunidades: str
    riesgos: str
    marcas_mencionadas: str
    temas_clave: str


class ProcessRequest(BaseModel):
    articles: list[RawArticle]


class ProcessResponse(BaseModel):
    articles_received: int
    articles_after_dedup: int
    new_articles: int
    analysis: Optional[LaguardiaAnalysis] = None
    raw_news_blob: str = ""
    insights: list[Insight] = []
