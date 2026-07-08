import json
import anthropic
from app.models.schemas import NormalizedArticle, Insight, LaguardiaAnalysis
from app.core.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """Eres un analista de inteligencia de mercado especializado en el sector de baños, cerámica, pavimentos y revestimientos en España.
Trabajas para Laguardia-Moreira, un distribuidor de materiales de baño y cerámica que compite con Porcelanosa, Roca, Cosentino, Grohe, Duravit, Geberit, Santos y Calvo y Munar.
Tu objetivo es identificar señales de mercado accionables para que el equipo comercial y de dirección tome decisiones informadas.
Responde siempre en JSON válido."""

USER_PROMPT_TEMPLATE = """Analiza las siguientes noticias del sector y genera un informe de inteligencia competitiva para Laguardia-Moreira.

NOTICIAS:
{news_block}

Devuelve un JSON con esta estructura exacta (sin markdown, JSON puro):
{{
  "raw_news_blob": "listado formateado de todas las noticias analizadas con fuente y titular",
  "analysis": {{
    "senales_relevantes": "2-4 párrafos sobre las señales más importantes del sector hoy",
    "early_signals": "tendencias emergentes y señales débiles que pueden crecer",
    "market_shifts": "cambios estructurales en el mercado, movimientos de competidores clave",
    "implicaciones": "qué implica todo esto para Laguardia-Moreira específicamente",
    "oportunidades": "oportunidades concretas que puede aprovechar Laguardia-Moreira",
    "riesgos": "riesgos y amenazas a vigilar",
    "marcas_mencionadas": "lista separada por comas de todas las marcas mencionadas en las noticias",
    "temas_clave": "lista separada por comas de los temas principales detectados"
  }},
  "insights": [
    {{
      "title": "título corto del insight",
      "summary": "resumen en 2-3 frases",
      "relevance": "alta | media | baja",
      "sources": ["url1", "url2"],
      "tags": ["tag1", "tag2"]
    }}
  ]
}}"""


def _strip_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def generate_insights(
    articles: list[NormalizedArticle],
) -> tuple[LaguardiaAnalysis | None, str, list[Insight]]:
    """Devuelve (analysis, raw_news_blob, insights)."""
    if not articles:
        return None, "", []

    news_block = "\n\n".join(
        f"[{a.source}] {a.title}\n{a.url}"
        for a in articles
    )

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT_TEMPLATE.format(news_block=news_block)}],
    )

    data = json.loads(_strip_fence(response.content[0].text))

    analysis = LaguardiaAnalysis(**data["analysis"]) if "analysis" in data else None
    raw_blob = data.get("raw_news_blob", news_block)
    insight_list = [Insight(**i) for i in data.get("insights", [])]

    return analysis, raw_blob, insight_list
