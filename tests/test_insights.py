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


def test_analysis_without_linkedin_draft_is_still_valid():
    from app.models.schemas import LaguardiaAnalysis
    campos = ["senales_relevantes", "early_signals", "market_shifts", "implicaciones", "oportunidades",
              "riesgos", "marcas_mencionadas", "temas_clave", "recomendacion_dia"]
    assert LaguardiaAnalysis(**{c: "" for c in campos}).post_linkedin == ""
