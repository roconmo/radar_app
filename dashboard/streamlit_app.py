import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SHEET_ID = "1uUEKEv6MEEFsSp-qY8aFHkDJ-CknhIY8PBTX0yfhzfE"
SHEET_NAME = "daily_reports"

st.set_page_config(page_title="Radar Moreira", page_icon="📡", layout="wide")

st.markdown("""
<style>
.recomendacion {
    background: #1a1f35;
    border-left: 4px solid #4a9eff;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    margin-bottom: 8px;
    font-size: 15px;
    line-height: 1.7;
}
.seccion-titulo {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 10px;
}
.oportunidad {
    background: #0d2818;
    border-left: 3px solid #50fa7b;
    border-radius: 0 6px 6px 0;
    padding: 10px 12px;
    margin-bottom: 8px;
    font-size: 13px;
    line-height: 1.5;
}
.riesgo {
    background: #2a1010;
    border-left: 3px solid #ff5555;
    border-radius: 0 6px 6px 0;
    padding: 10px 12px;
    margin-bottom: 8px;
    font-size: 13px;
    line-height: 1.5;
}
.tag  { background:#2d3250; color:#a0c4ff; border-radius:4px; padding:3px 9px; font-size:12px; margin:3px 3px; display:inline-block; }
.marca { background:#2d2050; color:#d0a0ff; border-radius:4px; padding:3px 9px; font-size:12px; margin:3px 3px; display:inline-block; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=1800)
def load_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    records = sheet.get_all_records()
    return pd.DataFrame(records)


try:
    df = load_data()
except Exception as e:
    st.error(f"Error cargando datos desde Google Sheets: {e}")
    st.stop()

if df.empty:
    st.warning("El Sheet no tiene datos todavía.")
    st.stop()

latest = df.iloc[-1]

# ── Cabecera ──────────────────────────────────────────────────────────────────
col_title, col_meta = st.columns([3, 1])
with col_title:
    st.title("📡 Radar Moreira")
with col_meta:
    fecha = str(latest.get("run_date", ""))
    st.markdown(f"<div style='text-align:right;color:#888;padding-top:18px'>{fecha}</div>", unsafe_allow_html=True)

# ── Recomendación del día ─────────────────────────────────────────────────────
recomendacion = str(latest.get("recomendacion_dia", "")).strip()
if recomendacion:
    st.markdown(f"<div class='recomendacion'><strong>💡 Recomendación del día</strong><br><br>{recomendacion}</div>", unsafe_allow_html=True)

st.divider()

# ── Señales · Early signals · Market shifts ───────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("<div class='seccion-titulo' style='color:#4a9eff'>📊 Señales relevantes</div>", unsafe_allow_html=True)
    st.markdown(str(latest.get("senales_relevantes", "—")).strip() or "—")

with c2:
    st.markdown("<div class='seccion-titulo' style='color:#ffb86c'>🔭 Early signals</div>", unsafe_allow_html=True)
    st.markdown(str(latest.get("early_signals", "—")).strip() or "—")

with c3:
    st.markdown("<div class='seccion-titulo' style='color:#bd93f9'>📈 Market shifts</div>", unsafe_allow_html=True)
    st.markdown(str(latest.get("market_shifts", "—")).strip() or "—")

st.divider()

# ── Implicaciones ─────────────────────────────────────────────────────────────
implicaciones = str(latest.get("implicaciones", "")).strip()
if implicaciones:
    st.markdown("**🎯 Implicaciones para Laguardia-Moreira**")
    st.markdown(implicaciones)
    st.divider()

# ── Oportunidades y riesgos ───────────────────────────────────────────────────
col_op, col_ri = st.columns(2)

def render_items(texto, css_class):
    for line in texto.strip().split("\n"):
        line = line.strip().lstrip("•-*0123456789. ").strip()
        if line:
            st.markdown(f"<div class='{css_class}'>{line}</div>", unsafe_allow_html=True)

with col_op:
    st.markdown("**✅ Oportunidades**")
    oportunidades = str(latest.get("oportunidades", "")).strip()
    if oportunidades:
        render_items(oportunidades, "oportunidad")
    else:
        st.caption("Sin datos")

with col_ri:
    st.markdown("**⚠️ Riesgos**")
    riesgos = str(latest.get("riesgos", "")).strip()
    if riesgos:
        render_items(riesgos, "riesgo")
    else:
        st.caption("Sin datos")

st.divider()

# ── Marcas y temas ────────────────────────────────────────────────────────────
col_m, col_t = st.columns(2)

with col_m:
    st.markdown("**🏷️ Marcas mencionadas**")
    marcas = str(latest.get("marcas_mencionadas", "")).strip()
    if marcas:
        html = "".join(f'<span class="marca">{m.strip()}</span>' for m in marcas.split(",") if m.strip())
        st.markdown(html, unsafe_allow_html=True)

with col_t:
    st.markdown("**🔑 Temas clave**")
    temas = str(latest.get("temas_clave", "")).strip()
    if temas:
        html = "".join(f'<span class="tag">{t.strip()}</span>' for t in temas.split(",") if t.strip())
        st.markdown(html, unsafe_allow_html=True)

st.divider()

# ── Histórico ─────────────────────────────────────────────────────────────────
with st.expander("📅 Histórico de informes"):
    cols_show = [c for c in ["run_date", "temas_clave", "marcas_mencionadas", "recomendacion_dia"] if c in df.columns]
    st.dataframe(
        df[cols_show].iloc[::-1].reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

if st.button("🔄 Actualizar datos"):
    st.cache_data.clear()
    st.rerun()
