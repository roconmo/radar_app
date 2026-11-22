import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test")

from app.services.insights import USER_PROMPT_TEMPLATE


def test_prompt_includes_date_and_keeps_json_example():
    prompt = USER_PROMPT_TEMPLATE.format(news_block="[roca] Titular", fecha="02/10/2026")
    assert "FECHA DE HOY: 02/10/2026" in prompt
    assert "[roca] Titular" in prompt
    assert '"marcas_mencionadas":' in prompt and "{" in prompt


def test_prompt_asks_for_linkedin_draft():
    prompt = USER_PROMPT_TEMPLATE.format(news_block="x", fecha="14/10/2026")
    assert '"post_linkedin":' in prompt


def test_prompt_does_not_ask_to_copy_the_news_list():
    prompt = USER_PROMPT_TEMPLATE.format(news_block="x", fecha="22/11/2026")
    assert '"raw_news_blob"' not in prompt


def test_gabriela_prompt_is_loaded_from_file():
    from app.services.insights import _gabriela_system_prompt
    texto = _gabriela_system_prompt()
    assert "Gabriela Tassile" in texto and texto.endswith("JSON válido.")


def test_gabriela_news_block_includes_short_text():
    from app.models.schemas import NormalizedArticle
    from app.services.insights import _gabriela_news_block, GABRIELA_CONTENT_CHARS
    art = NormalizedArticle(title="Congreso SEMI", url="https://a.com/1", source="mcb", content="x" * 2000)
    bloque = _gabriela_news_block([art])
    assert bloque.startswith("[mcb] Congreso SEMI\nhttps://a.com/1\n")
    assert bloque.count("x") == GABRIELA_CONTENT_CHARS


def test_gabriela_analysis_accepts_lists_and_missing_fields():
    from app.services.insights import _to_gabriela_analysis
    a = _to_gabriela_analysis({"resumen": "Hoy poco movimiento.", "oportunidades_inmediatas": ["Uno", "Dos"]})
    assert a.oportunidades_inmediatas == "Uno\nDos"
    assert a.accion_semana == ""


def test_analysis_without_linkedin_draft_is_still_valid():
    from app.models.schemas import LaguardiaAnalysis
    campos = ["senales_relevantes", "early_signals", "market_shifts", "implicaciones", "oportunidades",
              "riesgos", "marcas_mencionadas", "temas_clave", "recomendacion_dia"]
    assert LaguardiaAnalysis(**{c: "" for c in campos}).post_linkedin == ""
