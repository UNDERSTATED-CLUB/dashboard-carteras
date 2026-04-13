"""
╔══════════════════════════════════════════════════════════════╗
║         DASHBOARD FINANCIERO INTERACTIVO                     ║
║         Comparativa de Carteras de Inversión                 ║
╚══════════════════════════════════════════════════════════════╝

INSTRUCCIONES (3 PASOS):
  1. pip install -r requirements.txt
  2. streamlit run dashboard.py
  3. (Opcional) Subir a Streamlit Cloud → streamlit.io/cloud
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Financiero | Comparativa de Carteras",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  PALETA DE COLORES
# ─────────────────────────────────────────────
COLOR_RENTA_FIJA   = "#3B82F6"   # Azul
COLOR_RENTA_VAR    = "#10B981"   # Verde esmeralda
COLOR_CRIPTO       = "#F59E0B"   # Ámbar/dorado
COLOR_CARTERA1     = "#6366F1"   # Índigo (cartera clásica)
COLOR_CARTERA2     = "#EC4899"   # Rosa (cartera con cripto)
COLOR_BG           = "#0F172A"   # Azul marino oscuro
COLOR_SURFACE      = "#1E293B"   # Superficie elevada
COLOR_BORDER       = "#334155"   # Bordes

# ─────────────────────────────────────────────
#  CSS PERSONALIZADO
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

  html, body, [class*="css"] {{
      font-family: 'DM Sans', sans-serif;
      background-color: {COLOR_BG};
      color: #E2E8F0;
  }}

  .stApp {{
      background: linear-gradient(135deg, {COLOR_BG} 0%, #0D1B2A 100%);
  }}

  /* Cabecera principal */
  .main-header {{
      text-align: center;
      padding: 2.5rem 1rem 1.5rem;
      border-bottom: 1px solid {COLOR_BORDER};
      margin-bottom: 2rem;
  }}
  .main-header h1 {{
      font-family: 'Space Mono', monospace;
      font-size: 2.2rem;
      font-weight: 700;
      letter-spacing: -1px;
      background: linear-gradient(90deg, {COLOR_CARTERA1}, {COLOR_CARTERA2});
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0;
  }}
  .main-header p {{
      color: #94A3B8;
      font-size: 1rem;
      margin-top: 0.4rem;
      font-weight: 300;
  }}

  /* Tarjetas KPI */
  .kpi-card {{
      background: {COLOR_SURFACE};
      border: 1px solid {COLOR_BORDER};
      border-radius: 12px;
      padding: 1.2rem 1.4rem;
      text-align: center;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
  }}
  .kpi-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0,0,0,0.4);
  }}
  .kpi-label {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #64748B;
      font-weight: 500;
      margin-bottom: 0.4rem;
  }}
  .kpi-value {{
      font-family: 'Space Mono', monospace;
      font-size: 1.6rem;
      font-weight: 700;
      line-height: 1;
  }}
  .kpi-sub {{
      font-size: 0.75rem;
      color: #64748B;
      margin-top: 0.3rem;
  }}
  .positive {{ color: #10B981; }}
  .negative {{ color: #EF4444; }}
  .neutral  {{ color: #E2E8F0; }}

  /* Sección de título */
  .section-title {{
      font-family: 'Space Mono', monospace;
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #64748B;
      margin: 2rem 0 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid {COLOR_BORDER};
  }}

  /* Cartera badges */
  .badge {{
      display: inline-block;
      padding: 0.2rem 0.7rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.5px;
  }}
  .badge-c1 {{ background: rgba(99,102,241,0.2); color: {COLOR_CARTERA1}; border: 1px solid {COLOR_CARTERA1}; }}
  .badge-c2 {{ background: rgba(236,72,153,0.2); color: {COLOR_CARTERA2}; border: 1px solid {COLOR_CARTERA2}; }}

  /* Noticias */
  .news-item {{
      background: {COLOR_SURFACE};
      border: 1px solid {COLOR_BORDER};
      border-radius: 10px;
      padding: 0.9rem 1.1rem;
      margin-bottom: 0.6rem;
      transition: border-color 0.2s;
  }}
  .news-item:hover {{ border-color: {COLOR_CARTERA1}; }}
  .news-title {{
      font-size: 0.88rem;
      font-weight: 500;
      color: #CBD5E1;
      margin: 0 0 0.25rem;
  }}
  .news-meta {{
      font-size: 0.72rem;
      color: #475569;
  }}

  /* Divider */
  hr {{ border-color: {COLOR_BORDER} !important; }}

  /* Ocultar elementos de Streamlit */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 0 !important; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DEFINICIÓN DE CARTERAS
# ─────────────────────────────────────────────
INICIO = "2025-01-01"
HOY    = date.today().strftime("%Y-%m-%d")
INVERSION_TOTAL = 1000  # euros

# Pesos de cada activo por cartera
CARTERA_1 = {
    "TLT":  0.25,   # Renta fija
    "LQD":  0.25,   # Renta fija
    "TSLA": 0.25,   # Renta variable
    "AAPL": 0.25,   # Renta variable
}

CARTERA_2 = {
    "TLT":     0.20,  # Renta fija
    "LQD":     0.20,  # Renta fija
    "TSLA":    0.20,  # Renta variable
    "AAPL":    0.20,  # Renta variable
    "BTC-USD": 0.10,  # Cripto
    "ETH-USD": 0.10,  # Cripto
}

# Categoría de cada ticker (para colores)
CATEGORIAS = {
    "TLT":     "Renta Fija",
    "LQD":     "Renta Fija",
    "TSLA":    "Renta Variable",
    "AAPL":    "Renta Variable",
    "BTC-USD": "Cripto",
    "ETH-USD": "Cripto",
}

COLOR_CAT = {
    "Renta Fija":     COLOR_RENTA_FIJA,
    "Renta Variable": COLOR_RENTA_VAR,
    "Cripto":         COLOR_CRIPTO,
}

NOMBRES = {
    "TLT":     "TLT · Bono Gov. USA",
    "LQD":     "LQD · Bono Corp.",
    "TSLA":    "TSLA · Tesla",
    "AAPL":    "AAPL · Apple",
    "BTC-USD": "BTC · Bitcoin",
    "ETH-USD": "ETH · Ethereum",
}


# ─────────────────────────────────────────────
#  FUNCIONES DE DATOS
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)  # Cachear 1 hora para no saturar Yahoo Finance
def descargar_precios(tickers: list) -> pd.DataFrame:
    """Descarga precios de cierre ajustados de Yahoo Finance."""
    datos = yf.download(
        tickers,
        start=INICIO,
        end=HOY,
        auto_adjust=True,
        progress=False,
    )
    # Si solo hay un ticker, yfinance devuelve estructura diferente
    if isinstance(datos.columns, pd.MultiIndex):
        precios = datos["Close"]
    else:
        precios = datos[["Close"]].rename(columns={"Close": tickers[0]})
    return precios.dropna(how="all")


def calcular_evolucion(precios: pd.DataFrame, pesos: dict) -> pd.Series:
    """
    Calcula el valor total de la cartera día a día.
    Parte de INVERSION_TOTAL euros y aplica los pesos.
    """
    valor_cartera = pd.Series(0.0, index=precios.index)

    for ticker, peso in pesos.items():
        if ticker not in precios.columns:
            continue
        serie = precios[ticker].dropna()
        if serie.empty:
            continue
        # Precio inicial (primer día disponible)
        precio_inicial = serie.iloc[0]
        # Cantidad de activo comprada con la inversión asignada
        inversion_activo = INVERSION_TOTAL * peso
        unidades = inversion_activo / precio_inicial
        # Valor de ese activo cada día
        valor_activo = unidades * serie
        # Rellenar días sin datos con el último valor conocido
        valor_activo = valor_activo.reindex(precios.index).ffill()
        valor_cartera = valor_cartera + valor_activo

    return valor_cartera


def calcular_kpis(serie: pd.Series) -> dict:
    """Calcula KPIs financieros básicos a partir de la serie de valor."""
    valor_actual  = serie.iloc[-1]
    valor_inicial = serie.iloc[0]
    roi           = (valor_actual / valor_inicial - 1) * 100
    # Volatilidad anualizada (desviación estándar de retornos diarios × √252)
    retornos      = serie.pct_change().dropna()
    volatilidad   = retornos.std() * (252 ** 0.5) * 100
    # Máximo drawdown
    maximo        = serie.cummax()
    drawdown      = ((serie - maximo) / maximo * 100).min()
    return {
        "valor_actual": valor_actual,
        "roi":          roi,
        "volatilidad":  volatilidad,
        "drawdown":     drawdown,
        "ganancia":     valor_actual - valor_inicial,
    }


@st.cache_data(ttl=1800)
def obtener_noticias() -> list:
    """
    Obtiene titulares financieros recientes desde Yahoo Finance RSS.
    Devuelve lista de dicts con 'titulo', 'fuente', 'link'.
    """
    noticias = []
    feeds = [
        ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
        ("Yahoo Cripto",  "https://finance.yahoo.com/rss/2.0/headline?s=BTC-USD&region=US&lang=en-US"),
    ]
    headers = {"User-Agent": "Mozilla/5.0"}

    for fuente, url in feeds:
        try:
            resp = requests.get(url, headers=headers, timeout=6)
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")[:5]
            for item in items:
                titulo = item.find("title")
                link   = item.find("link")
                pub    = item.find("pubDate")
                noticias.append({
                    "titulo": titulo.text.strip() if titulo else "Sin título",
                    "fuente": fuente,
                    "link":   link.text.strip() if link else "#",
                    "fecha":  pub.text[:16] if pub else "",
                })
        except Exception:
            pass  # Si falla la red, simplemente no mostramos noticias de esa fuente

    # Fallback si no se obtuvieron noticias
    if not noticias:
        noticias = [
            {"titulo": "⚠️ No se pudieron cargar noticias en este momento.",
             "fuente": "Sistema", "link": "#", "fecha": ""},
            {"titulo": "Consulta Yahoo Finance, Bloomberg o El Economista para noticias.",
             "fuente": "Sugerencia", "link": "https://finance.yahoo.com", "fecha": ""},
        ]
    return noticias[:12]


# ─────────────────────────────────────────────
#  GRÁFICOS
# ─────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#94A3B8", size=12),
    xaxis=dict(gridcolor="#1E293B", linecolor="#334155", zerolinecolor="#334155"),
    yaxis=dict(gridcolor="#1E293B", linecolor="#334155", zerolinecolor="#334155"),
    margin=dict(l=40, r=20, t=40, b=40),
    hovermode="x unified",
)


def grafico_evolucion(serie: pd.Series, nombre: str, color: str) -> go.Figure:
    """Gráfico de área de la evolución de una cartera."""
    fig = go.Figure()

    # Área rellena bajo la curva
    fig.add_trace(go.Scatter(
        x=serie.index,
        y=serie.values,
        fill="tozeroy",
        fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0,2,4)) + (0.12,)}",
        line=dict(color=color, width=2.5),
        name=nombre,
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Valor: %{y:.2f}€<extra></extra>",
    ))

    # Línea de inversión inicial
    fig.add_hline(
        y=INVERSION_TOTAL,
        line_dash="dot",
        line_color="#475569",
        annotation_text=" Inversión inicial",
        annotation_font_color="#475569",
        annotation_font_size=11,
    )

    fig.update_layout(
        title=dict(text=nombre, font=dict(color="#E2E8F0", size=14, family="Space Mono")),
        showlegend=False,
        **PLOT_LAYOUT,
    )
    fig.update_yaxes(ticksuffix="€")
    return fig


def grafico_comparativo(s1: pd.Series, s2: pd.Series) -> go.Figure:
    """Gráfico comparativo de ambas carteras en el mismo lienzo."""
    fig = go.Figure()

    for serie, nombre, color in [
        (s1, "🔵 Cartera 1 · Clásica",   COLOR_CARTERA1),
        (s2, "🔴 Cartera 2 · Con Cripto", COLOR_CARTERA2),
    ]:
        fig.add_trace(go.Scatter(
            x=serie.index,
            y=serie.values,
            mode="lines",
            name=nombre,
            line=dict(color=color, width=2.5),
            hovertemplate=f"<b>{nombre}</b><br>%{{x|%d %b %Y}}: %{{y:.2f}}€<extra></extra>",
        ))

    fig.add_hline(
        y=INVERSION_TOTAL,
        line_dash="dot",
        line_color="#475569",
        annotation_text=" 1.000€ iniciales",
        annotation_font_color="#475569",
        annotation_font_size=11,
    )

    fig.update_layout(
        title=dict(
            text="Comparativa de Carteras · Evolución conjunta",
            font=dict(color="#E2E8F0", size=14, family="Space Mono")
        ),
        legend=dict(
            bgcolor="rgba(30,41,59,0.8)",
            bordercolor="#334155",
            borderwidth=1,
        ),
        **PLOT_LAYOUT,
    )
    fig.update_yaxes(ticksuffix="€")
    return fig


def grafico_pie(pesos: dict, titulo: str) -> go.Figure:
    """Pie chart de composición de cartera."""
    labels  = [NOMBRES.get(t, t) for t in pesos]
    values  = list(pesos.values())
    colors  = [COLOR_CAT[CATEGORIAS[t]] for t in pesos]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color=COLOR_BG, width=2)),
        textfont=dict(size=11, family="DM Sans"),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=titulo, font=dict(color="#E2E8F0", size=13, family="Space Mono")),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(
            font=dict(color="#94A3B8", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
    )
    return fig


def grafico_retornos_diarios(s1: pd.Series, s2: pd.Series) -> go.Figure:
    """Histograma comparativo de retornos diarios."""
    r1 = s1.pct_change().dropna() * 100
    r2 = s2.pct_change().dropna() * 100

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=r1, name="Cartera 1", opacity=0.65,
        marker_color=COLOR_CARTERA1, nbinsx=40,
    ))
    fig.add_trace(go.Histogram(
        x=r2, name="Cartera 2", opacity=0.65,
        marker_color=COLOR_CARTERA2, nbinsx=40,
    ))
    fig.update_layout(
        barmode="overlay",
        title=dict(
            text="Distribución de Retornos Diarios (%)",
            font=dict(color="#E2E8F0", size=14, family="Space Mono"),
        ),
        legend=dict(bgcolor="rgba(30,41,59,0.8)", bordercolor="#334155", borderwidth=1),
        **PLOT_LAYOUT,
    )
    fig.update_xaxes(ticksuffix="%")
    return fig


# ─────────────────────────────────────────────
#  HELPERS DE RENDERIZADO
# ─────────────────────────────────────────────
def kpi_card(label: str, valor, suffix="", positivo=None):
    """Renderiza una tarjeta KPI HTML."""
    if positivo is True:
        cls = "positive"
    elif positivo is False:
        cls = "negative"
    else:
        cls = "neutral"

    if isinstance(valor, float):
        valor_str = f"{valor:+.2f}" if positivo is not None else f"{valor:.2f}"
    else:
        valor_str = str(valor)

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {cls}">{valor_str}{suffix}</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  APP PRINCIPAL
# ─────────────────────────────────────────────
def main():
    # ── CABECERA ──────────────────────────────
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard Financiero</h1>
        <p>Comparativa de Carteras de Inversión · Enero 2025 → Hoy · 1.000€ iniciales</p>
    </div>
    """, unsafe_allow_html=True)

    # ── DESCARGA DE DATOS ─────────────────────
    todos_tickers = list(set(list(CARTERA_1.keys()) + list(CARTERA_2.keys())))

    with st.spinner("⏳ Descargando datos de mercado desde Yahoo Finance…"):
        precios = descargar_precios(todos_tickers)

    if precios.empty:
        st.error("❌ No se pudieron obtener datos. Comprueba tu conexión a internet.")
        return

    # ── CÁLCULO DE CARTERAS ───────────────────
    evol_c1 = calcular_evolucion(precios, CARTERA_1)
    evol_c2 = calcular_evolucion(precios, CARTERA_2)

    # Eliminar días sin datos (inicio donde no hay precios de todos los activos)
    evol_c1 = evol_c1[evol_c1 > 0]
    evol_c2 = evol_c2[evol_c2 > 0]

    kpis_c1 = calcular_kpis(evol_c1)
    kpis_c2 = calcular_kpis(evol_c2)

    # ── PERÍODO ───────────────────────────────
    st.caption(f"📅 Período: **{INICIO}** → **{HOY}**  |  Datos: Yahoo Finance (yfinance)")

    # ══════════════════════════════════════════
    #  SECCIÓN 1: KPIs
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">📌 KPIs · Indicadores Clave</div>', unsafe_allow_html=True)

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        st.markdown('<span class="badge badge-c1">CARTERA 1 · Clásica</span>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Valor Actual",   kpis_c1["valor_actual"], "€", None)
        with c2: kpi_card("ROI",            kpis_c1["roi"],          "%", kpis_c1["roi"] >= 0)
        with c3: kpi_card("Volatilidad",    kpis_c1["volatilidad"],  "%", None)
        with c4: kpi_card("Max. Drawdown",  kpis_c1["drawdown"],     "%", False)

    with col_h2:
        st.markdown('<span class="badge badge-c2">CARTERA 2 · Con Cripto</span>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Valor Actual",   kpis_c2["valor_actual"], "€", None)
        with c2: kpi_card("ROI",            kpis_c2["roi"],          "%", kpis_c2["roi"] >= 0)
        with c3: kpi_card("Volatilidad",    kpis_c2["volatilidad"],  "%", None)
        with c4: kpi_card("Max. Drawdown",  kpis_c2["drawdown"],     "%", False)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════
    #  SECCIÓN 2: EVOLUCIÓN INDIVIDUAL
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">📈 Evolución Individual de Carteras</div>', unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(
            grafico_evolucion(evol_c1, "Cartera 1 · Clásica (Renta Fija + Variable)", COLOR_CARTERA1),
            use_container_width=True,
        )
    with col_g2:
        st.plotly_chart(
            grafico_evolucion(evol_c2, "Cartera 2 · Con Cripto (RF + RV + BTC + ETH)", COLOR_CARTERA2),
            use_container_width=True,
        )

    # ══════════════════════════════════════════
    #  SECCIÓN 3: COMPARATIVA CONJUNTA
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">⚖️ Comparativa Conjunta</div>', unsafe_allow_html=True)

    st.plotly_chart(grafico_comparativo(evol_c1, evol_c2), use_container_width=True)

    # ══════════════════════════════════════════
    #  SECCIÓN 4: COMPOSICIÓN Y DISTRIBUCIÓN
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">🥧 Composición y Distribución de Retornos</div>', unsafe_allow_html=True)

    col_p1, col_p2, col_hist = st.columns([1, 1, 2])

    with col_p1:
        st.plotly_chart(grafico_pie(CARTERA_1, "Cartera 1"), use_container_width=True)
    with col_p2:
        st.plotly_chart(grafico_pie(CARTERA_2, "Cartera 2"), use_container_width=True)
    with col_hist:
        st.plotly_chart(grafico_retornos_diarios(evol_c1, evol_c2), use_container_width=True)

    # ── Leyenda de colores ────────────────────
    st.markdown(f"""
    <div style="display:flex;gap:1.5rem;padding:0.8rem 0;flex-wrap:wrap;">
        <span style="color:{COLOR_RENTA_FIJA};font-size:0.82rem;">■ Renta Fija (TLT, LQD)</span>
        <span style="color:{COLOR_RENTA_VAR};font-size:0.82rem;">■ Renta Variable (TSLA, AAPL)</span>
        <span style="color:{COLOR_CRIPTO};font-size:0.82rem;">■ Cripto (BTC, ETH)</span>
        <span style="color:{COLOR_CARTERA1};font-size:0.82rem;">■ Cartera 1 Clásica</span>
        <span style="color:{COLOR_CARTERA2};font-size:0.82rem;">■ Cartera 2 Con Cripto</span>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    #  SECCIÓN 5: DATOS DE ACTIVOS
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">📋 Datos de Activos Individuales</div>', unsafe_allow_html=True)

    filas = []
    for ticker in todos_tickers:
        if ticker not in precios.columns:
            continue
        serie = precios[ticker].dropna()
        if len(serie) < 2:
            continue
        ret = (serie.iloc[-1] / serie.iloc[0] - 1) * 100
        vol = serie.pct_change().dropna().std() * (252 ** 0.5) * 100
        filas.append({
            "Activo":     NOMBRES.get(ticker, ticker),
            "Categoría":  CATEGORIAS.get(ticker, "–"),
            "Precio Inicial (USD)": f"{serie.iloc[0]:.2f}",
            "Precio Actual (USD)":  f"{serie.iloc[-1]:.2f}",
            "Retorno (%)": f"{ret:+.2f}%",
            "Volatilidad (%)": f"{vol:.2f}%",
        })

    df_tabla = pd.DataFrame(filas)
    st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True,
    )

    # ══════════════════════════════════════════
    #  SECCIÓN 6: NOTICIAS FINANCIERAS
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">📰 Noticias Financieras Recientes</div>', unsafe_allow_html=True)

    with st.spinner("Cargando noticias…"):
        noticias = obtener_noticias()

    col_n1, col_n2 = st.columns(2)
    for i, noticia in enumerate(noticias):
        col = col_n1 if i % 2 == 0 else col_n2
        with col:
            st.markdown(f"""
            <div class="news-item">
                <div class="news-title">
                    <a href="{noticia['link']}" target="_blank"
                       style="color:#CBD5E1;text-decoration:none;">
                        {noticia['titulo']}
                    </a>
                </div>
                <div class="news-meta">🗞 {noticia['fuente']} &nbsp;·&nbsp; {noticia['fecha']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── PIE DE PÁGINA ─────────────────────────
    st.markdown("""
    <hr style="margin-top:3rem;">
    <div style="text-align:center;color:#334155;font-size:0.75rem;padding:1rem 0 2rem;">
        Datos proporcionados por Yahoo Finance · Solo con fines educativos · No es asesoramiento financiero
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()
