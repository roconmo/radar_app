import json
import anthropic
from app.models.schemas import NormalizedArticle, Insight
from app.core.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """Eres un analista de inteligencia de mercado especializado en el sector inmobiliario y de inversión en España.
Recibes un listado de noticias normalizadas y debes generar insights accionables.
Responde siempre en JSON válido con el schema indicado."""

USER_PROMPT_TEMPLATE = """Analiza las siguientes noticias y genera insights relevantes.

NOTICIAS:
{news_block}

Devuelve un JSON con esta estructura exacta:
{{
  "insights": [
    {{
      "title": "título corto del insight",
      "summary": "resumen del insight en 2-3 frases",
      "relevance": "alta | media | baja",
      "sources": ["url1", "url2"],
      "tags": ["tag1", "tag2"]
    }}
  ]
}}"""


def generate_insights(articles: list[NormalizedArticle]) -> list[Insight]:
    if not articles:
        return []

    news_block = "\n\n".join(
        f"[{a.source}] {a.title}\n{a.url}\n{a.content[:500]}"
        for a in articles
    )

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT_TEMPLATE.format(news_block=news_block)}],
    )

    raw = response.content[0].text.strip()
    # Claude a veces envuelve el JSON en ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    return [Insight(**item) for item in data["insights"]]
