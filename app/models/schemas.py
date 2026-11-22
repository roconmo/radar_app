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
    recomendacion_dia: str
    post_linkedin: str = ""  # borrador para Marketing, nunca se publica automáticamente


class GabrielaAnalysis(BaseModel):
    """Informe comercial de Gabriela Tassile (catering). Cada campo es texto listo para el correo."""
    resumen: str = ""
    oportunidades_inmediatas: str = ""
    nuevas_organizaciones: str = ""
    senales_mercado: str = ""
    accion_semana: str = ""


class ArticleOut(BaseModel):
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    analizada: bool  # False si quedó fuera del límite de artículos enviados a Claude


class ProcessRequest(BaseModel):
    articles: list[RawArticle]
    empresa: str = "laguardia"  # sin este campo, el informe es el de Laguardia-Moreira


class ProcessResponse(BaseModel):
    empresa: str = "laguardia"
    articles_received: int
    articles_after_dedup: int
    new_articles: int
    analysis: Optional[LaguardiaAnalysis] = None
    analysis_gabriela: Optional[GabrielaAnalysis] = None
    raw_news_blob: str = ""
    insights: list[Insight] = []
    new_articles_list: list[ArticleOut] = []
