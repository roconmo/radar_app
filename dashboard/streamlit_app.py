import sqlite3
import json
import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

DB_PATH = os.getenv("HISTORY_DB_PATH", "data/history.db")

st.set_page_config(page_title="Radar App", page_icon="📡", layout="wide")

# ── Estilos ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.kpi-box { background:#1e2130; border-radius:8px; padding:16px; border-top:3px solid; }
.insight-card { background:#1e2130; border-left:4px solid; border-radius:0 8px 8px 0; padding:12px 14px; margin-bottom:10px; }
.tag-chip { background:#2d3250; color:#a0c4ff; border-radius:4px; padding:2px 8px; font-size:12px; margin-right:4px; display:inline-block; }
</style>
""", unsafe_allow_html=True)


# ── Datos ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data(days: int):
    if not os.path.exists(DB_PATH):
        return {k: pd.DataFrame() for k in ["runs", "articles", "insights"]}

    since = (datetime.now() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_PATH)

    runs = pd.read_sql(
        "SELECT * FROM pipeline_runs WHERE run_at >= ? ORDER BY run_at DESC",
        conn, params=(since,), parse_dates=["run_at"]
    )
    articles = pd.read_sql(
        "SELECT * FROM articles WHERE processed_at >= ? ORDER BY processed_at DESC",
        conn, params=(since,), parse_dates=["processed_at", "published_at"]
    )
    insights_df = pd.read_sql(
        "SELECT * FROM insights WHERE created_at >= ? ORDER BY created_at DESC",
        conn, params=(since,), parse_dates=["created_at"]
    )
    conn.close()

    if not insights_df.empty:
        insights_df["tags"] = insights_df["tags"].apply(
            lambda x: json.loads(x) if x else []
        )
        insights_df["sources"] = insights_df["sources"].apply(
            lambda x: json.loads(x) if x else []
        )

    return {"runs": runs, "articles": articles, "insights": insights_df}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📡 Radar App")
    st.divider()

    period = st.selectbox(
        "Período", ["7 días", "30 días", "90 días"], index=1
    )
    days = int(period.split()[0])

    st.subheader("Filtros")
    relevancia = st.multiselect(
        "Relevancia", ["alta", "media", "baja"],
        default=["alta", "media"]
    )

    data = load_data(days)
    ins = data["insights"]
    arts = data["articles"]
    runs = data["runs"]

    if not arts.empty:
        fuentes = arts["source"].unique().tolist()
        fuentes_sel = st.multiselect("Fuentes", fuentes, default=fuentes)
    else:
        fuentes_sel = []

    st.divider()
    if not runs.empty:
        last = runs.iloc[0]
        st.success(f"**Última ejecución**\n\n{last['run_at'].strftime('%d/%m/%Y %H:%M')}")
        st.caption(f"{int(last['new_articles'])} nuevas · {int(last['insights_generated'])} insights")
    else:
        st.info("Sin ejecuciones registradas aún")

    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()


# ── Página principal ──────────────────────────────────────────────────────────
st.title("Dashboard")
st.caption(f"Inteligencia de mercado · últimos {days} días")

if runs.empty:
    st.warning("No hay datos todavía. El dashboard se llenará tras la primera ejecución del pipeline.")
    st.stop()

# Aplicar filtros
if not ins.empty and relevancia:
    ins = ins[ins["relevance"].isin(relevancia)]
if not arts.empty and fuentes_sel:
    arts = arts[arts["source"].isin(fuentes_sel)]


# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

total_recibidas = int(runs["articles_received"].sum()) if not runs.empty else 0
total_nuevas = int(runs["new_articles"].sum()) if not runs.empty else 0
total_insights = int(runs["insights_generated"].sum()) if not runs.empty else 0
alta_count = int((ins["relevance"] == "alta").sum()) if not ins.empty else 0
ratio_filtrado = round((1 - total_nuevas / total_recibidas) * 100) if total_recibidas else 0

k1.metric("Noticias recibidas", f"{total_recibidas:,}", help=f"Últimos {days} días")
k2.metric("Artículos nuevos", f"{total_nuevas:,}")
k3.metric("Insights generados", f"{total_insights:,}")
k4.metric("Alta relevancia", f"{alta_count}", help="Insights con relevancia alta")
k5.metric("Ratio filtrado", f"{ratio_filtrado}%", help="% de noticias descartadas por duplicadas o ya vistas")

st.divider()

# ── Gráfica de actividad + fuentes ────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Artículos nuevos por día")
    if not arts.empty:
        daily = (
            arts.set_index("processed_at")
            .resample("D")["id"].count()
            .rename("Artículos nuevos")
        )
        st.line_chart(daily, color="#4a9eff")
    else:
        st.info("Sin datos en el período seleccionado")

with col2:
    st.subheader("Por fuente")
    if not arts.empty:
        fuente_counts = arts["source"].value_counts().reset_index()
        fuente_counts.columns = ["Fuente", "Artículos"]
        st.bar_chart(fuente_counts.set_index("Fuente"), color="#50fa7b")
    else:
        st.info("Sin datos")

st.divider()

# ── Insights recientes ────────────────────────────────────────────────────────
col_ins, col_tags = st.columns([2, 1])

with col_ins:
    st.subheader("Insights recientes")
    if not ins.empty:
        colors = {"alta": "#ff5555", "media": "#ffb86c", "baja": "#6272a4"}
        for _, row in ins.head(10).iterrows():
            color = colors.get(row["relevance"], "#888")
            tags_html = "".join(
                f'<span class="tag-chip">{t}</span>' for t in (row["tags"] or [])
            )
            fecha = row["created_at"].strftime("%d/%m") if pd.notna(row["created_at"]) else ""
            st.markdown(f"""
<div class="insight-card" style="border-color:{color}">
  <div style="display:flex;justify-content:space-between;margin-bottom:4px">
    <strong style="font-size:14px">{row['title']}</strong>
    <span style="color:{color};font-size:11px;font-weight:700;text-transform:uppercase">{row['relevance']} · {fecha}</span>
  </div>
  <div style="color:#aaa;font-size:12px;margin-bottom:8px">{row['summary']}</div>
  {tags_html}
</div>""", unsafe_allow_html=True)
    else:
        st.info("No hay insights con los filtros seleccionados")

with col_tags:
    st.subheader("Tags frecuentes")
    if not ins.empty:
        all_tags = [t for tags in ins["tags"] for t in (tags or [])]
        if all_tags:
            tag_series = pd.Series(all_tags).value_counts().head(12).reset_index()
            tag_series.columns = ["Tag", "Menciones"]
            st.bar_chart(tag_series.set_index("Tag"), color="#bd93f9")
        else:
            st.info("Sin tags")

    st.subheader("Por relevancia")
    if not ins.empty:
        rel_counts = ins["relevance"].value_counts().reset_index()
        rel_counts.columns = ["Relevancia", "Total"]
        st.bar_chart(rel_counts.set_index("Relevancia"), color="#ffb86c")

st.divider()

# ── Tabla de artículos ────────────────────────────────────────────────────────
with st.expander("📰 Artículos procesados"):
    if not arts.empty:
        show_cols = ["title", "source", "published_at", "processed_at"]
        show_cols = [c for c in show_cols if c in arts.columns]
        st.dataframe(
            arts[show_cols].rename(columns={
                "title": "Título", "source": "Fuente",
                "published_at": "Publicado", "processed_at": "Procesado"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Sin artículos en el período")
