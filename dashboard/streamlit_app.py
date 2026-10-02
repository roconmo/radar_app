import html
import re
import unicodedata
from collections import Counter

import gspread
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.oauth2.service_account import Credentials

SHEET_ID = "1uUEKEv6MEEFsSp-qY8aFHkDJ-CknhIY8PBTX0yfhzfE"
TZ = "Europe/Madrid"

C = dict(card="#131a2e", border="#232c48", text="#e6e9f2", muted="#8a93ad", blue="#4a9eff",
         green="#50fa7b", red="#ff5555", orange="#ffb86c", purple="#bd93f9", cyan="#8be9fd", pink="#ff79c6")
PALETTE = [C["blue"], C["purple"], C["orange"], C["green"], C["cyan"], C["pink"], "#f1fa8c", "#a0c4ff",
           "#ff9580", "#6272a4", "#d0a0ff", "#7ee0b5"]

# Roca y Santos son palabras comunes: se buscan con mayúscula o como nombre de fuente
COMPETIDORES = {
    "Roca": re.compile(r"\bRoca\b|\[roca\]"),
    "Porcelanosa": re.compile(r"porcelanosa", re.I),
    "Cosentino": re.compile(r"cosentino|silestone|dekton", re.I),
    "Grohe": re.compile(r"\bgrohe\b", re.I),
    "Hansgrohe": re.compile(r"hansgrohe|\baxor\b", re.I),
    "Duravit": re.compile(r"duravit", re.I),
    "Geberit": re.compile(r"geberit", re.I),
    "Santos": re.compile(r"\bSantos\b|\[santos\]"),
    "Calvo y Munar": re.compile(r"calvo\s*y\s*munar|calvoymunar", re.I),
    "J Abad (proveedor)": re.compile(r"\bj\.?\s?abad\b|jabad", re.I),
}

TEMAS = {
    "Canal prescriptor": r"prescrip|arquitect|interioris|contract|especificaci",
    "Instaladores y reforma": r"instalador|reform|rehabilit|colocaci|profesional",
    "Sostenibilidad y energía": r"sostenib|eficien|energ|descarboni|circular|hídric|agua|biomaterial|ecológ|carbono|reciclad",
    "Ferias y eventos": r"feria|cevisama|cersaie|evento|premio|casa decor|salone|design week|jornada|congreso",
    "Internacionalización": r"internacional|export|exterior|global",
    "Precios y costes": r"precio|coste|tarifa|margen|inflaci|arancel|rentabilidad",
    "Vivienda y construcción": r"vivienda|obra|construcci|promot|inmobiliari|alquiler|licitaci|urban",
    "Diseño y producto": r"diseño|colecci|lanzamiento|tendencia|grifer|color|modular|cerámic|porcelánic|mueble|wellness|ducha|superficie",
    "Distribución y retail": r"distribu|retail|showroom|tienda|bricolaje|desintermedi|e-commerce|online|canal",
    "Empresas y directivos": r"nombramiento|director|gerente|\bceo\b|presiden|relevo|adquisici|fusi[oó]n|compra|inversi|resultados|facturaci",
    "Digital y tecnología": r"digital|tecnolog|\bia\b|inteligencia artificial|software|\bbim\b|smart|automatiz",
}
TEMAS = {k: re.compile(v, re.I) for k, v in TEMAS.items()}

SECCIONES = ["senales_relevantes", "early_signals", "market_shifts", "implicaciones",
             "oportunidades", "riesgos", "marcas_mencionadas", "temas_clave", "recomendacion_dia"]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

st.set_page_config(page_title="Radar Moreira", page_icon="📡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stMarkdown, .stText, button, input { font-family: 'Inter', sans-serif !important; }
.block-container { padding-top: 2.2rem; max-width: 1440px; }
.hero { display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:12px;
  padding: 28px 32px; border-radius: 18px; border: 1px solid #232c48; margin-bottom: 18px;
  background: radial-gradient(900px 260px at 0% 0%, rgba(74,158,255,.28), transparent 60%),
              radial-gradient(700px 260px at 100% 0%, rgba(189,147,249,.20), transparent 60%), #131a2e; }
.hero-kicker { color:#8a93ad; font-size:12px; letter-spacing:1.6px; text-transform:uppercase; font-weight:600; }
.hero-title { font-size:42px; font-weight:800; letter-spacing:-1.2px; line-height:1.1;
  background: linear-gradient(90deg,#ffffff,#a0c4ff 60%,#d0a0ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hero-meta { text-align:right; color:#8a93ad; font-size:13px; line-height:1.6; }
.hero-meta b { color:#e6e9f2; font-size:17px; }
.kpi { background:#131a2e; border:1px solid #232c48; border-radius:14px; padding:16px 18px; min-height:118px; }
.kpi-label { color:#8a93ad; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.9px; }
.kpi-value { font-size:30px; font-weight:800; margin-top:6px; color:#e6e9f2; letter-spacing:-.5px; line-height:1.15; }
.kpi-value.small { font-size:22px; }
.kpi-delta { font-size:12px; margin-top:4px; color:#8a93ad; }
.up { color:#50fa7b; } .down { color:#ff5555; }
.section-title { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#8a93ad; margin:4px 0 10px; }
.recomendacion { background: linear-gradient(90deg, rgba(74,158,255,.16), rgba(74,158,255,.04)); border-left:4px solid #4a9eff;
  border-radius:0 12px 12px 0; padding:18px 22px; margin-bottom:12px; font-size:15px; line-height:1.7; }
.recomendacion .lbl { font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#4a9eff; margin-bottom:6px; }
.oportunidad { background:#0d2818; border-left:3px solid #50fa7b; border-radius:0 8px 8px 0; padding:10px 12px; margin-bottom:8px; font-size:13px; line-height:1.55; }
.riesgo { background:#2a1010; border-left:3px solid #ff5555; border-radius:0 8px 8px 0; padding:10px 12px; margin-bottom:8px; font-size:13px; line-height:1.55; }
.tag { background:#1f2747; color:#a0c4ff; border-radius:6px; padding:3px 9px; font-size:12px; margin:3px; display:inline-block; }
.marca { background:#2a2050; color:#d0a0ff; border-radius:6px; padding:3px 9px; font-size:12px; margin:3px; display:inline-block; }
.nuevo { background:rgba(255,184,108,.14); color:#ffb86c; border:1px solid rgba(255,184,108,.35); border-radius:6px; padding:3px 9px; font-size:12px; margin:3px; display:inline-block; }
.news { padding:10px 0; border-bottom:1px solid #232c48; font-size:14px; line-height:1.45; }
.news:last-child { border-bottom:none; }
.news a { color:#e6e9f2; text-decoration:none; } .news a:hover { color:#4a9eff; }
.news-meta { color:#8a93ad; font-size:12px; margin-top:3px; }
.pill { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:600; background:#1d2540; color:#a0c4ff; margin-right:6px; }
.comp-card { background:#131a2e; border:1px solid #232c48; border-radius:12px; padding:12px 14px; margin-bottom:8px; }
.comp-name { font-weight:700; font-size:14px; } .comp-date { color:#8a93ad; font-size:12px; float:right; }
.comp-news { font-size:13px; margin-top:4px; line-height:1.45; } .comp-news a { color:#c9d1e6; text-decoration:none; } .comp-news a:hover { color:#4a9eff; }
.snippet { color:#c9d1e6; font-size:13px; line-height:1.6; margin:6px 0; }
mark { background: rgba(255,184,108,.35); color: inherit; padding:0 2px; border-radius:3px; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { font-weight:600; padding: 8px 14px; }
</style>
""", unsafe_allow_html=True)


# ── Datos ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def spreadsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    return gspread.authorize(creds).open_by_key(SHEET_ID)


@st.cache_data(ttl=1800)
def load(tab: str) -> pd.DataFrame:
    return pd.DataFrame(spreadsheet().worksheet(tab).get_all_records())


ITEM_RX = re.compile(r"\[([a-z0-9][a-z0-9\-]*)\]\s*(.*?)(?=\s*\[[a-z0-9][a-z0-9\-]*\]|\Z)", re.S)
URL_RX = re.compile(r"https?://[^\s|]+")


def split_blob(blob: str) -> list[dict]:
    items = []
    for fuente, resto in ITEM_RX.findall(blob):
        url = URL_RX.search(resto)
        titular = URL_RX.sub("", resto).strip(" |—–-\n\t")
        if titular:
            items.append({"fuente": fuente, "titular": titular, "url": url.group(0) if url else ""})
    return items


def prepare_reports(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    for col in SECCIONES + ["raw_news_blob"]:
        df[col] = df.get(col, "").astype(str).str.strip()
    df["ts"] = pd.to_datetime(df["run_date"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")
    df["fecha"] = df["ts"].dt.tz_convert(TZ).dt.tz_localize(None).dt.normalize()
    df = df.drop_duplicates("fecha", keep="last").reset_index(drop=True)
    df["noticias"] = df["raw_news_blob"].apply(split_blob)
    df["n_noticias"] = df["noticias"].str.len()
    df["semana"] = df["fecha"].dt.to_period("W-SUN").dt.start_time
    return df


def prepare_fuentes(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["activa"] = df["Activo"].astype(str).str.strip().str.upper().isin(["TRUE", "1", "SI", "SÍ", "✔"])
    df = df[df["activa"]].copy()

    def estado(v):
        v = str(v).strip()
        if v.upper().startswith("OK"):
            return "Operativa"
        if v.upper().startswith("BLOQUEADO"):
            return "Vía Jina"
        return "Con incidencia" if v else "Sin comprobar"

    df["estado"] = df["ok?"].apply(estado)
    return df


def competitor_hits(noticias: list[dict], marcas: str) -> dict:
    hits = {}
    for nombre, rx in COMPETIDORES.items():
        n = sum(1 for it in noticias if rx.search(f"[{it['fuente']}] {it['titular']}"))
        hits[nombre] = n if n or not rx.search(marcas) else 1
    return hits


def tema_buckets(temas: str) -> Counter:
    c = Counter()
    for t in (x.strip() for x in temas.split(",")):
        if t:
            for bloque, rx in TEMAS.items():
                if rx.search(t):
                    c[bloque] += 1
    return c


# ── Utilidades de presentación ────────────────────────────────────────────────
def fecha_larga(d) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_corta(d) -> str:
    return f"{d.day} {MESES[d.month - 1][:3]}"


def esc(s) -> str:
    return html.escape(str(s))


def link(titular: str, url: str) -> str:
    if url.startswith("http"):
        return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(titular)}</a>'
    return esc(titular)


def kpi(label: str, value, delta_html: str = "", small: bool = False) -> str:
    cls = "kpi-value small" if small else "kpi-value"
    return (f'<div class="kpi"><div class="kpi-label">{esc(label)}</div>'
            f'<div class="{cls}">{esc(value)}</div><div class="kpi-delta">{delta_html}</div></div>')


def delta(cur: int, prev: int | None, texto: str) -> str:
    if prev is None:
        return esc(texto)
    d = cur - prev
    if d == 0:
        return f"= {esc(texto)}"
    cls, signo = ("up", "▲") if d > 0 else ("down", "▼")
    return f'<span class="{cls}">{signo} {abs(d)}</span> {esc(texto)}'


def pretty(fig, height=360):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["text"], family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", y=-0.18, title=None),
        hoverlabel=dict(bgcolor=C["card"], bordercolor=C["border"], font_color=C["text"]),
    )
    fig.update_xaxes(gridcolor=C["border"], zeroline=False, title=None)
    fig.update_yaxes(gridcolor=C["border"], zeroline=False, title=None)
    return fig


def chart(fig, height=360):
    st.plotly_chart(pretty(fig, height), width="stretch", config={"displayModeBar": False})


def lista_items(texto: str) -> list[str]:
    partes = re.split(r"\n+|(?<=\s)(?=\d{1,2}\.\s)", texto)
    return [p.strip().lstrip("•-*0123456789. ").strip() for p in partes if p.strip().lstrip("•-*0123456789. ").strip()]


def sin_acentos(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn").lower()


# ── Carga ─────────────────────────────────────────────────────────────────────
try:
    rep = prepare_reports(load("daily_reports"))
    fuentes = prepare_fuentes(load("fuentes"))
except Exception as e:
    st.error(f"Error cargando datos desde Google Sheets: {e}")
    st.stop()

if rep.empty:
    st.warning("El Sheet no tiene informes todavía.")
    st.stop()

comp = pd.DataFrame([
    {"fecha": r.fecha, "semana": r.semana, "competidor": k, "menciones": v}
    for r in rep.itertuples() for k, v in competitor_hits(r.noticias, r.marcas_mencionadas).items()
])
temas = pd.DataFrame([
    {"fecha": r.fecha, "semana": r.semana, "bloque": k, "n": v}
    for r in rep.itertuples() for k, v in tema_buckets(r.temas_clave).items()
], columns=["fecha", "semana", "bloque", "n"])
marcas = pd.DataFrame([
    {"fecha": r.fecha, "marca": m.strip()}
    for r in rep.itertuples() for m in r.marcas_mencionadas.split(",") if m.strip()
], columns=["fecha", "marca"])
noticias = pd.DataFrame([
    {"fecha": r.fecha, **it} for r in rep.itertuples() for it in r.noticias
], columns=["fecha", "fuente", "titular", "url"])

# ── Barra lateral ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Radar Moreira")
    if st.button("Actualizar datos", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Fuente: Google Sheets «Informe periódico». Los datos se refrescan solos cada 30 minutos.")

st.markdown(f"""
<div class="hero">
  <div><div class="hero-kicker">Inteligencia de mercado · Laguardia-Moreira</div>
  <div class="hero-title">Radar Moreira</div></div>
  <div class="hero-meta">Último informe<br><b>{esc(fecha_larga(rep['fecha'].max()).capitalize())}</b><br>{len(rep)} informes desde el {esc(fecha_corta(rep['fecha'].min()))}</div>
</div>
""", unsafe_allow_html=True)

PERIODOS = {"7 días": 7, "30 días": 30, "Todo": None}
st.session_state.setdefault("periodo_previo", "30 días")


def mantener_periodo():
    # Volver a pulsar la opción activa la desmarcaría: se restaura la anterior
    if st.session_state.periodo is None:
        st.session_state.periodo = st.session_state.periodo_previo
    st.session_state.periodo_previo = st.session_state.periodo


col_lbl, col_sel = st.columns([3, 2], vertical_alignment="center")
with col_sel:
    periodo = st.segmented_control("Periodo de análisis", list(PERIODOS), default="30 días", key="periodo",
                                   on_change=mantener_periodo, label_visibility="collapsed", width="stretch")
with col_lbl:
    st.markdown(f"<div class='section-title' style='margin:0'>Periodo de análisis: {esc(periodo.lower())}</div>", unsafe_allow_html=True)

ultimo = rep["fecha"].max()
dias = PERIODOS[periodo]
ini = ultimo - pd.Timedelta(days=dias - 1) if dias else rep["fecha"].min()
prev_ini = ini - pd.Timedelta(days=dias) if dias else None


def en_periodo(df):
    return df[df["fecha"] >= ini]


def en_previo(df):
    return df[(df["fecha"] >= prev_ini) & (df["fecha"] < ini)] if dias else df.iloc[0:0]


hay_previo = len(en_previo(rep)) > 0


# ── KPIs ──────────────────────────────────────────────────────────────────────
last = rep.iloc[-1]
prev = rep.iloc[-2] if len(rep) > 1 else None
comp_last = comp[comp["fecha"] == last.fecha]
comp_prev = comp[comp["fecha"] == prev.fecha] if prev is not None else None
n_comp_last = int((comp_last["menciones"] > 0).sum())
n_comp_prev = int((comp_prev["menciones"] > 0).sum()) if comp_prev is not None else None

rank_p = en_periodo(comp).groupby("competidor")["menciones"].sum().sort_values(ascending=False)
top_comp = rank_p.index[0] if len(rank_p) and rank_p.iloc[0] > 0 else "Sin datos"

operativas = int(fuentes["estado"].isin(["Operativa", "Vía Jina"]).sum())
incidencias = int((fuentes["estado"] == "Con incidencia").sum())
inc_html = f'<span class="down">{incidencias} con incidencia</span>' if incidencias else '<span class="up">todas operativas</span>'

k = st.columns(5)
k[0].markdown(kpi("Noticias citadas", int(last.n_noticias),
                  delta(int(last.n_noticias), int(prev.n_noticias) if prev is not None else None, "vs informe anterior")), unsafe_allow_html=True)
k[1].markdown(kpi("Competidores hoy", f"{n_comp_last}/{len(COMPETIDORES)}",
                  delta(n_comp_last, n_comp_prev, "vs informe anterior")), unsafe_allow_html=True)
k[2].markdown(kpi("Más activo", top_comp,
                  f"{int(rank_p.iloc[0]) if len(rank_p) else 0} noticias · {esc(periodo.lower())}", small=True), unsafe_allow_html=True)
k[3].markdown(kpi("Informes", len(en_periodo(rep)),
                  delta(len(en_periodo(rep)), len(en_previo(rep)), "vs periodo anterior") if hay_previo
                  else f"en {esc(periodo.lower())}"), unsafe_allow_html=True)
k[4].markdown(kpi("Fuentes operativas", f"{operativas}/{len(fuentes)}", inc_html), unsafe_allow_html=True)

st.write("")
tab_inf, tab_comp, tab_tend, tab_fuen, tab_bus = st.tabs(
    ["Informe del día", "Competencia", "Tendencias", "Fuentes", "Buscador"])

# ── Informe del día ───────────────────────────────────────────────────────────
with tab_inf:
    fechas = list(rep["fecha"].sort_values(ascending=False))
    sel = st.selectbox("Informe", fechas, format_func=lambda d: fecha_larga(d).capitalize(), label_visibility="collapsed")
    row = rep[rep["fecha"] == sel].iloc[0]

    if row.recomendacion_dia:
        st.markdown(f'<div class="recomendacion"><div class="lbl">Recomendación del día</div>{esc(row.recomendacion_dia)}</div>',
                    unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, campo, titulo, color in [
        (c1, "senales_relevantes", "Señales relevantes", C["blue"]),
        (c2, "early_signals", "Early signals", C["orange"]),
        (c3, "market_shifts", "Market shifts", C["purple"]),
    ]:
        with col, st.container(border=True, height=420):
            st.markdown(f"<div class='section-title' style='color:{color}'>{titulo}</div>", unsafe_allow_html=True)
            st.markdown(row[campo] or "Sin datos")

    if row.implicaciones:
        with st.container(border=True):
            st.markdown("<div class='section-title' style='color:#8be9fd'>Implicaciones para Laguardia-Moreira</div>", unsafe_allow_html=True)
            st.markdown(row.implicaciones)

    col_op, col_ri = st.columns(2)
    for col, campo, titulo, css in [(col_op, "oportunidades", "Oportunidades", "oportunidad"),
                                    (col_ri, "riesgos", "Riesgos", "riesgo")]:
        with col:
            st.markdown(f"<div class='section-title'>{titulo}</div>", unsafe_allow_html=True)
            items = lista_items(row[campo])
            if items:
                st.markdown("".join(f"<div class='{css}'>{esc(i)}</div>" for i in items), unsafe_allow_html=True)
            else:
                st.caption("Sin datos")

    col_m, col_t = st.columns(2)
    with col_m:
        st.markdown("<div class='section-title'>Marcas mencionadas</div>", unsafe_allow_html=True)
        st.markdown("".join(f'<span class="marca">{esc(m.strip())}</span>' for m in row.marcas_mencionadas.split(",") if m.strip()) or "—",
                    unsafe_allow_html=True)
    with col_t:
        st.markdown("<div class='section-title'>Temas clave</div>", unsafe_allow_html=True)
        st.markdown("".join(f'<span class="tag">{esc(t.strip())}</span>' for t in row.temas_clave.split(",") if t.strip()) or "—",
                    unsafe_allow_html=True)

    if row.noticias:
        st.write("")
        with st.expander(f"Noticias citadas en este informe ({len(row.noticias)})"):
            st.markdown("".join(
                f'<div class="news"><span class="pill">{esc(it["fuente"])}</span>{link(it["titular"], it["url"])}</div>'
                for it in row.noticias), unsafe_allow_html=True)

# ── Competencia ───────────────────────────────────────────────────────────────
with tab_comp:
    st.caption("Noticias cuyo titular menciona a cada competidor, más su aparición en «marcas mencionadas».")
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown(f"<div class='section-title'>Ranking de presencia · {esc(periodo.lower())}</div>", unsafe_allow_html=True)
        prev_rank = en_previo(comp).groupby("competidor")["menciones"].sum()
        rk = rank_p.reset_index().sort_values("menciones")
        rk["previo"] = rk["competidor"].map(prev_rank).fillna(0).astype(int)
        rk["color"] = [C["orange"] if "proveedor" in c else C["blue"] for c in rk["competidor"]]
        fig = go.Bar(x=rk["menciones"], y=rk["competidor"], orientation="h", marker_color=rk["color"],
                     text=rk["menciones"], textposition="outside", cliponaxis=False,
                     customdata=rk["previo"],
                     hovertemplate="<b>%{y}</b><br>%{x} noticias<br>Periodo anterior: %{customdata}<extra></extra>")
        chart(go.Figure(fig), height=380)

        st.markdown("<div class='section-title'>Mapa de calor semanal</div>", unsafe_allow_html=True)
        hm = en_periodo(comp).pivot_table(index="competidor", columns="semana", values="menciones", aggfunc="sum", fill_value=0)
        hm = hm.loc[rank_p.index]
        fig = go.Figure(go.Heatmap(
            z=hm.values, x=[fecha_corta(d) for d in hm.columns], y=hm.index,
            colorscale=[[0, C["card"]], [0.001, "#1b2d55"], [1, C["blue"]]], showscale=False, xgap=3, ygap=3,
            hovertemplate="<b>%{y}</b><br>Semana del %{x}<br>%{z} noticias<extra></extra>"))
        fig.update_yaxes(autorange="reversed")
        chart(fig, height=340)

    with right:
        st.markdown("<div class='section-title'>Última noticia de cada competidor</div>", unsafe_allow_html=True)
        cards = []
        for nombre, rx in COMPETIDORES.items():
            hit = noticias[noticias.apply(lambda r: bool(rx.search(f"[{r.fuente}] {r.titular}")), axis=1)] if len(noticias) else noticias
            if len(hit):
                h = hit.iloc[-1]
                cards.append((h.fecha, f'<div class="comp-card"><span class="comp-date">{esc(fecha_corta(h.fecha))}</span>'
                                       f'<div class="comp-name">{esc(nombre)}</div>'
                                       f'<div class="comp-news"><span class="pill">{esc(h.fuente)}</span>{link(h.titular, h.url)}</div></div>'))
            else:
                aviso = ("Citado en «marcas mencionadas», sin titular propio" if comp.loc[comp["competidor"] == nombre, "menciones"].sum()
                         else "Sin noticias en los informes")
                cards.append((pd.Timestamp.min, f'<div class="comp-card"><div class="comp-name">{esc(nombre)}</div>'
                                                f'<div class="comp-news" style="color:#8a93ad">{aviso}</div></div>'))
        st.markdown("".join(c for _, c in sorted(cards, key=lambda x: x[0], reverse=True)), unsafe_allow_html=True)

# ── Tendencias ────────────────────────────────────────────────────────────────
with tab_tend:
    st.caption("Los temas clave de cada informe agrupados en bloques del sector.")
    left, right = st.columns([2, 3], gap="large")
    tp = en_periodo(temas).groupby("bloque")["n"].sum()
    tprev = en_previo(temas).groupby("bloque")["n"].sum()

    with left:
        st.markdown(f"<div class='section-title'>Peso de cada bloque · {esc(periodo.lower())}</div>", unsafe_allow_html=True)
        tb = pd.DataFrame({"n": tp}).reindex(TEMAS.keys()).fillna(0).astype(int)
        tb["previo"] = tprev.reindex(tb.index).fillna(0).astype(int)
        tb = tb.sort_values("n")
        etiquetas = [f"{n}" + (f"  ({'+' if n - p >= 0 else ''}{n - p})" if hay_previo else "") for n, p in zip(tb["n"], tb["previo"])]
        colores = [C["green"] if (n > p and hay_previo) else (C["red"] if (n < p and hay_previo) else C["purple"]) for n, p in zip(tb["n"], tb["previo"])]
        fig = go.Figure(go.Bar(x=tb["n"], y=tb.index, orientation="h", marker_color=colores, text=etiquetas,
                               textposition="outside", cliponaxis=False,
                               hovertemplate="<b>%{y}</b><br>%{x} menciones<extra></extra>"))
        chart(fig, height=430)
        if hay_previo:
            st.caption("Verde: sube frente al periodo anterior. Rojo: baja.")

    with right:
        st.markdown("<div class='section-title'>Evolución semanal</div>", unsafe_allow_html=True)
        ts = en_periodo(temas).groupby(["semana", "bloque"])["n"].sum().reset_index()
        orden = list(tp.sort_values(ascending=False).index)
        fig = px.area(ts, x="semana", y="n", color="bloque", category_orders={"bloque": orden},
                      color_discrete_sequence=PALETTE, line_shape="spline")
        fig.update_traces(line_width=1, hovertemplate="%{y}<extra>%{fullData.name}</extra>")
        fig.update_layout(hovermode="x unified", legend=dict(font=dict(size=11)))
        chart(fig, height=430)

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"<div class='section-title'>Marcas más mencionadas · {esc(periodo.lower())}</div>", unsafe_allow_html=True)
        mc = en_periodo(marcas)["marca"].value_counts().head(15).sort_values()
        fig = go.Figure(go.Bar(x=mc.values, y=mc.index, orientation="h", marker_color=C["purple"],
                               text=mc.values, textposition="outside", cliponaxis=False,
                               hovertemplate="<b>%{y}</b><br>%{x} informes<extra></extra>"))
        chart(fig, height=440)
    with right:
        st.markdown("<div class='section-title'>Temas emergentes</div>", unsafe_allow_html=True)
        corte = ultimo - pd.Timedelta(days=13)
        vistos = {sin_acentos(t.strip()) for s in rep[rep["fecha"] < corte]["temas_clave"] for t in s.split(",") if t.strip()}
        nuevos = []
        for s in rep[rep["fecha"] >= corte].sort_values("fecha", ascending=False)["temas_clave"]:
            for t in (x.strip() for x in s.split(",")):
                if t and sin_acentos(t) not in vistos and sin_acentos(t) not in {sin_acentos(n) for n in nuevos}:
                    nuevos.append(t)
        st.caption("Temas que aparecen en los últimos 14 días y nunca antes.")
        st.markdown("".join(f'<span class="nuevo">{esc(t)}</span>' for t in nuevos[:40]) or "Sin temas nuevos", unsafe_allow_html=True)

# ── Fuentes ───────────────────────────────────────────────────────────────────
with tab_fuen:
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown("<div class='section-title'>Estado de las fuentes</div>", unsafe_allow_html=True)
        estados = fuentes["estado"].value_counts()
        colores_estado = {"Operativa": C["green"], "Vía Jina": C["blue"], "Con incidencia": C["red"], "Sin comprobar": C["muted"]}
        fig = go.Figure(go.Pie(labels=estados.index, values=estados.values, hole=0.68, sort=False,
                               marker=dict(colors=[colores_estado[e] for e in estados.index], line=dict(color="#0b1020", width=3)),
                               textinfo="value", hovertemplate="<b>%{label}</b><br>%{value} fuentes<extra></extra>"))
        fig.add_annotation(text=f"<b style='font-size:30px'>{operativas}</b><br>de {len(fuentes)} activas",
                           showarrow=False, font=dict(color=C["text"], size=13))
        chart(fig, height=300)
        st.caption("«Vía Jina»: la web bloquea peticiones directas, pero el Radar la lee sin problema a través de Jina.")

    with right:
        st.markdown("<div class='section-title'>Fuentes con incidencia</div>", unsafe_allow_html=True)
        inc = fuentes[fuentes["estado"].isin(["Con incidencia", "Sin comprobar"])][["Nombre", "URL", "ok?"]]
        if len(inc):
            st.dataframe(inc.rename(columns={"ok?": "Último chequeo"}), hide_index=True, width="stretch",
                         column_config={"URL": st.column_config.LinkColumn("URL")})
        else:
            st.success("Todas las fuentes activas responden correctamente.")
        with st.expander(f"Ver las {len(fuentes)} fuentes activas"):
            st.dataframe(fuentes[["Nombre", "Tipo", "estado", "ok?", "URL"]].rename(columns={"estado": "Estado", "ok?": "Último chequeo"}),
                         hide_index=True, width="stretch", column_config={"URL": st.column_config.LinkColumn("URL")})

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown("<div class='section-title'>Noticias citadas por informe</div>", unsafe_allow_html=True)
        rp = en_periodo(rep)
        fig = go.Figure(go.Bar(x=rp["fecha"], y=rp["n_noticias"], marker_color=C["cyan"],
                               hovertemplate="%{x|%d/%m/%Y}<br>%{y} noticias<extra></extra>"))
        chart(fig, height=320)
    with right:
        st.markdown(f"<div class='section-title'>Fuentes que más aportan · {esc(periodo.lower())}</div>", unsafe_allow_html=True)
        fc = en_periodo(noticias)["fuente"].value_counts().head(12).sort_values()
        fig = go.Figure(go.Bar(x=fc.values, y=fc.index, orientation="h", marker_color=C["blue"],
                               text=fc.values, textposition="outside", cliponaxis=False,
                               hovertemplate="<b>%{y}</b><br>%{x} noticias<extra></extra>"))
        chart(fig, height=320)
    st.caption("Cuenta solo las noticias que el informe cita, que son una muestra de todas las analizadas.")

# ── Buscador ──────────────────────────────────────────────────────────────────
with tab_bus:
    q = st.text_input("Buscar en todos los informes", placeholder="Ej.: Porcelanosa, Cevisama, aranceles, grifería…")
    if q.strip():
        qn = sin_acentos(q.strip())
        hl = re.compile(re.escape(q.strip()), re.I)
        resultados = []
        for r in rep.sort_values("fecha", ascending=False).itertuples():
            tits = [it for it in r.noticias if qn in sin_acentos(it["titular"])]
            trozos = []
            for campo in SECCIONES:
                texto = getattr(r, campo)
                pos = sin_acentos(texto).find(qn)
                if pos >= 0:
                    a, b = max(0, pos - 140), min(len(texto), pos + len(qn) + 160)
                    trozos.append((campo, ("…" if a else "") + texto[a:b] + ("…" if b < len(texto) else "")))
            if tits or trozos:
                resultados.append((r, tits, trozos))

        st.caption(f"{len(resultados)} informes contienen «{q.strip()}».")
        nombres = {"senales_relevantes": "Señales", "early_signals": "Early signals", "market_shifts": "Market shifts",
                   "implicaciones": "Implicaciones", "oportunidades": "Oportunidades", "riesgos": "Riesgos",
                   "marcas_mencionadas": "Marcas", "temas_clave": "Temas", "recomendacion_dia": "Recomendación"}
        for r, tits, trozos in resultados[:30]:
            with st.container(border=True):
                st.markdown(f"**{fecha_larga(r.fecha).capitalize()}**")
                body = "".join(f'<div class="news"><span class="pill">{esc(it["fuente"])}</span>{link(it["titular"], it["url"])}</div>' for it in tits)
                body += "".join(f'<div class="snippet"><span class="pill">{nombres[c]}</span>{hl.sub(lambda m: f"<mark>{m.group(0)}</mark>", esc(t))}</div>'
                                for c, t in trozos[:3])
                st.markdown(body, unsafe_allow_html=True)
    else:
        st.caption("Busca una marca, un tema o una palabra en los titulares y en todos los análisis desde julio.")
