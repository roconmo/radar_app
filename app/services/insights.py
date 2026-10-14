import json
from datetime import date

import anthropic
from app.models.schemas import NormalizedArticle, Insight, LaguardiaAnalysis
from app.core.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """Eres un analista de inteligencia de mercado especializado en el sector de baños, cerámica, pavimentos y revestimientos en España.
Trabajas para Laguardia-Moreira, un distribuidor de materiales de baño y cerámica.

COMPETIDORES DIRECTOS a vigilar: Porcelanosa, Roca, Cosentino, Grohe, Duravit, Geberit, Santos, Calvo y Munar.
PROVEEDOR CLAVE a monitorizar: J Abad (jabadcodelco.net) — sus movimientos afectan directamente al catálogo y precios de Laguardia-Moreira.

Las noticias pueden venir tanto de prensa sectorial (interempresas, periodicoazulejo, etc.) como de las webs propias de los competidores y del proveedor.
Tu objetivo es identificar señales de mercado accionables para que el equipo comercial y de dirección tome decisiones informadas.
Responde siempre en JSON válido."""

USER_PROMPT_TEMPLATE = """Analiza las siguientes noticias del sector y genera un informe de inteligencia competitiva para Laguardia-Moreira.

FECHA DE HOY: {fecha}. Úsala como referencia para cualquier plazo o trimestre que menciones.

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
    "marcas_mencionadas": "lista separada por comas SOLO de marcas comerciales, fabricantes y distribuidores del sector (baño, cerámica, pavimentos, revestimientos, grifería, sanitarios, mobiliario de baño, superficies, ACS y climatización) que aparezcan en las noticias. NO incluyas ferias, eventos, medios, plataformas web, asociaciones, estudios de arquitectura, personas ni empresas de otros sectores, y no añadas aclaraciones entre paréntesis. Si no hay ninguna, devuelve una cadena vacía",
    "temas_clave": "lista separada por comas de los temas principales detectados",
    "recomendacion_dia": "UNA acción concreta y específica que el equipo comercial de Laguardia-Moreira debería hacer hoy basándose en las noticias analizadas",
    "post_linkedin": "borrador de post para la página de empresa de Laguardia-Moreira en LinkedIn, que el departamento de Marketing revisará y adaptará. Elige UNA noticia del día interesante para clientes, interioristas y profesionales de la reforma (tendencias, materiales, diseño, sostenibilidad, normativa). Voz de empresa, cercana y profesional, en primera persona del plural. 120-180 palabras: una primera línea que enganche, el dato o la novedad explicada con hechos que aparezcan en la noticia (sin inventar cifras), por qué importa a quien reforma un baño o una cocina, y una pregunta final para abrir conversación. Termina con la línea 'Fuente: <url de la noticia>' y 3-4 hashtags del sector. No critiques ni compares con competidores y no menciones estrategia interna, oportunidades ni riesgos del informe. Si ninguna noticia del día da para un buen post, devuelve exactamente: 'Hoy no hay una noticia con interés suficiente para un post.'"
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


MAX_ARTICLES = 80  # evita respuestas truncadas por límite de tokens


def generate_insights(
    articles: list[NormalizedArticle],
) -> tuple[LaguardiaAnalysis | None, str, list[Insight]]:
    """Devuelve (analysis, raw_news_blob, insights)."""
    if not articles:
        return None, "", []

    # Limitar para evitar que la respuesta de Claude se corte
    articles = articles[:MAX_ARTICLES]

    news_block = "\n\n".join(
        f"[{a.source}] {a.title}\n{a.url}"
        for a in articles
    )

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT_TEMPLATE.format(
            news_block=news_block, fecha=date.today().strftime("%d/%m/%Y"))}],
    )

    data = json.loads(_strip_fence(response.content[0].text))

    analysis = LaguardiaAnalysis(**data["analysis"]) if "analysis" in data else None
    raw_blob = data.get("raw_news_blob", news_block)
    insight_list = [Insight(**i) for i in data.get("insights", [])]

    return analysis, raw_blob, insight_list
