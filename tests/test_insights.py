import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test")

from app.services.insights import USER_PROMPT_TEMPLATE


def test_prompt_includes_date_and_keeps_json_example():
    prompt = USER_PROMPT_TEMPLATE.format(news_block="[roca] Titular", fecha="02/10/2026")
    assert "FECHA DE HOY: 02/10/2026" in prompt
    assert "[roca] Titular" in prompt
    assert '"marcas_mencionadas":' in prompt and "{" in prompt
