import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date
import re

# ==========================================
# BLOQUE 0: CONFIGURACIÓN Y ESTILOS VISUALES
# ==========================================
st.set_page_config(layout="wide", page_title="Master Command by PS")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1 { text-align: right; }
    
    .table-container {
        width: 100%;
        overflow-x: auto;
        max-height: 550px;
        overflow-y: auto;
        margin-bottom: 2rem;
        border: 1px solid #333;
    }
    
    .titanes-scroll {
        width: 100%;
        max-height: 460px;
        overflow-y: auto;
        overflow-x: auto;
        margin-bottom: 2rem;
        border: 1px solid #333333;
    }

    table { width: 100%; border-collapse: separate; border-spacing: 0; color: #E0E0E0; font-family: 'Inter', sans-serif; font-size: 13px; }

    /* Encabezados Superiores (Agrupación) */
    .group-header {
        background-color: #161a21 !important;
        color: #888888 !important;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid #444444 !important;
        text-align: center !important;
    }

    thead tr:nth-child(1) th { position: sticky; top: 0; z-index: 10; }

    /* Encabezados de Columna */
    thead tr:nth-child(2) th {
        position: sticky;
        top: 36px;
        background-color: #1E1E24 !important;
        color: #FFFFFF;
        z-index: 10;
        padding: 10px;
        border-bottom: 2px solid #333333;
        white-space: nowrap;
    }

    /* Primera columna pegada (Nombre) */
    tbody td:first-child, thead tr:nth-child(2) th:first-child {
        position: sticky;
        left: 0;
        z-index: 11;
        text-align: left;
        border-right: 2px solid #333333;
        background-color: #161a21 !important;
    }

    thead tr:nth-child(1) th:first-child, thead tr:nth-child(2) th:first-child { z-index: 12; background-color: #1E1E24 !important; }

    td {
        padding: 8px 12px;
        text-align: center;
        border-bottom: 1px solid #262730;
        white-space: nowrap;
        background-color: #0E1117;
    }

    .tv-link { color: #2962FF; text-decoration: none; font-weight: bold; }
    .tv-link:hover { text-decoration: underline; color: #448AFF; }
    
    div[data-testid="metric-container"] {
        background-color: #161a21;
        border: 1px solid #333333;
        padding: 15px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOQUE 1: DICCIONARIO MAESTRO COMPLETO
# ==========================================
ACTIVOS = {
    "MAJOR INDICES": {
        "S&P 500 (^GSPC)": "^GSPC", "MSCI World (URTH)": "URTH", "NASDAQ 100 (^NDX)": "^NDX",
        "Euro Stoxx 50 (^STOXX50E)": "^STOXX50E", "MSCI Emerging Markets (EEM)": "EEM", 
        "Russell 2000 (^RUT)": "^RUT", "S&P 500 Equal Weight (RSP)": "RSP", "VIX Volatility (^VIX)": "^VIX"
    },
    "TITANES GLOBALES (15)": {
        "Apple (AAPL)": "AAPL", "Microsoft (MSFT)": "MSFT", "Alphabet (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN", "NVIDIA (NVDA)": "NVDA", "Meta Platforms (META)": "META",
        "Tesla (TSLA)": "TSLA", "Berkshire Hathaway (BRK-B)": "BRK-B", "Eli Lilly (LLY)": "LLY",
        "JPMorgan Chase (JPM)": "JPM", "Visa (V)": "V", "Broadcom (AVGO)": "AVGO",
        "Novo Nordisk (NVO)": "NVO", "LVMH (LVMUY)": "LVMUY", "ASML (ASML)": "ASML" 
    },
    "CURRENCIES": {
        "EUR / USD (EURUSD=X)": "EURUSD=X", "EUR / GBP (EURGBP=X)": "EURGBP=X", "EUR / JPY (EURJPY=X)": "EURJPY=X",
        "USD / EUR (USDEUR=X)": "USDEUR=X", "USD / GBP (USDGBP=X)": "USDGBP=X", "USD / JPY (USDJPY=X)": "USDJPY=X"
    },
    "US TREASURY YIELD CURVE (Tasas %)": {
        "13-Week T-Bill (^IRX)": "^IRX", "5-Year T-Note (^FVX)": "^FVX", "10-Year T-Note (^TNX)": "^TNX", "30-Year T-Bond (^TYX)": "^TYX"
    },
    "BONDS (US ETFs - Precios)": {
        "US Treasury 0-1Y ETF (SHV)": "SHV", "US Treasury 20Y+ ETF (TLT)": "TLT", "Intl Gov Bonds ETF (BNDX)": "BNDX"
    },
    "COMMODITIES": {
        "Oil Brent (BZ=F)": "BZ=F", "Gold (GC=F)": "GC=F", "Silver (SI=F)": "SI=F",
        "Gold / Silver Ratio (GSR)": "GSR",
        "Copper (HG=F)": "HG=F", "Soybeans (ZS=F)": "ZS=F", "Bitcoin (BTC-USD)": "BTC-USD"
    },
    "GLOBAL FACTORS (US ETFs)": {
        "Large Cap Value (IVE)": "IVE", "Large Cap Growth (IVW)": "IVW", "Small Cap Value (IWN)": "IWN",
        "Small Cap Growth (IWO)": "IWO", "Value (VLUE)": "VLUE", "Quality (QUAL)": "QUAL", "Dividend (VYMI)": "VYMI"
    },
    "US SECTORS (US ETFs)": {
        "Technology (XLK)": "XLK", "Healthcare (XLV)": "XLV", "Financials (XLF)": "XLF",
        "Cons Discretionary (XLY)": "XLY", "Communication (XLC)": "XLC", "Industrials (XLI)": "XLI",
        "Cons Staples (XLP)": "XLP", "Energy (XLE)": "XLE", "Utilities (XLU)": "XLU", "Real Estate (XLRE)": "XLRE"
    },
    "EUROPE": {
        "UK FTSE 100 (^FTSE)": "^FTSE", "France CAC 40 (^FCHI)": "^FCHI", "Germany DAX (^GDAXI)": "^GDAXI",
        "Netherlands AEX (^AEX)": "^AEX", "Spain IBEX 35 (^IBEX)": "^IBEX", "Italy FTSE MIB (FTSEMIB.MI)": "FTSEMIB.MI"
    },
    "ASIA & LATAM (US ETFs)": {
        "Japan (EWJ)": "EWJ", "South Korea (EWY)": "EWY", "India (INDA)": "INDA",
        "China (MCHI)": "MCHI", "Brazil (EWZ)": "EWZ", "Mexico (EWW)": "EWW", "Argentina Merval CCL (MERVAL_USD)": "MERVAL_USD" 
    }
}

TICKERS_AUXILIARES = ["^MERV", "GGAL.BA", "GGAL"]

# ==========================================
# BLOQUE 2: LINKS A TRADINGVIEW
# ==========================================
def get_tv_url(ticker):
    tv_mapping = {
        "^GSPC": "SPX", "^NDX": "NDX", "^DJI": "DJI", "^FTSE": "UKX",
        "^IBEX": "IBC", "^GDAXI": "DAX", "^STOXX50E": "STOXX50",
        "^VIX": "VIX", "^IRX": "US03MY", "^FVX": "US05Y", "^TNX": "US10Y",
        "^TYX": "US30Y", "GSR": "XAUXAG"
    }
    if ticker in tv_mapping: symbol = tv_mapping[ticker]
    elif "MERVAL" in ticker: symbol = "MERV"
    else: symbol = ticker.replace('=X', '').replace('=F', '').replace('-', '').replace('^', '')
    return f"https://www.tradingview.com/chart/?symbol={symbol}"

# ==========================================
# BLOQUE 3: MOTORES DE DESCARGA DE DATOS
# ==========================================
@st.cache_data(ttl=300) 
def obtener_precios():
    all_tickers = []
    for cat in ACTIVOS.values(): all_tickers.extend(list(cat.values()))
    
    if "MERVAL_USD" in all_tickers: all_tickers.remove("MERVAL_USD")
    if "GSR" in all_tickers: all_tickers.remove("GSR")
        
    all_tickers.extend(TICKERS_AUXILIARES)
    all_tickers = list(set(all_tickers)) 
    
    try:
        data = yf.download(all_tickers, period="10y", interval="1d", auto_adjust=False)
        if isinstance(data.columns, pd.MultiIndex):
            df_precios = data['Adj Close'] if 'Adj Close' in data.columns.levels[0] else data['Close']
            df_volumen = data['Volume']
        else:
            df_precios, df_volumen = data, pd.DataFrame()
            
        df_precios.index = pd.to_datetime(df_precios.index).tz_localize(None).normalize()
        if not df_volumen.empty:
            df_volumen.index = pd.to_datetime(df_volumen.index).tz_localize(None).normalize()
        
        merv, ggal_ba, ggal_us = df_precios['^MERV'].ffill(), df_precios['GGAL.BA'].ffill(), df_precios['GGAL'].ffill()    
        df_precios['MERVAL_USD'] = merv / (ggal_ba / (ggal_us * 10))
        
        if 'GC=F' in df_precios.columns and 'SI=F' in df_precios.columns:
            df_precios['GSR'] = df_precios['GC=F'] / df_precios['SI=F']
            
        hora_actualizacion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        return df_precios, df_volumen, hora_actualizacion
    except: return pd.DataFrame(), pd.DataFrame(), None

# OPTIMIZACIÓN 1: Caching Estricto TTL 24 horas (86400 segundos) para datos macro
@st.cache_data(ttl=86400)
def obtener_macro_fred():
    try:
        def fetch_fred(series_id):
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
            df = pd.read_csv(url, index_col='DATE', parse_dates=True)
            df.columns = [series_id]
            df[series_id] = pd.to_numeric(df[series_id], errors='coerce')
            return df.dropna()

        fed_df = fetch_fred('FEDFUNDS')
        cpi_df = fetch_fred('CPIAUCSL')
        unrate_df = fetch_fred('UNRATE')
        walcl_df = fetch_fred('WALCL')

        fed_funds = fed_df['FEDFUNDS'].iloc[-1]
        unrate = unrate_df['UNRATE'].iloc[-1]

        cpi_latest = cpi_df['CPIAUCSL'].iloc[-1]
        cpi_yoy = ((cpi_latest / cpi_df['CPIAUCSL'].iloc[cpi_df.index.get_indexer([cpi_df.index[-1] - pd.DateOffset(years=1)], method='nearest')[0]]) - 1) * 100

        walcl_latest = walcl_df['WALCL'].iloc[-1]
        walcl_mom = ((walcl_latest / walcl_df['WALCL'].iloc[walcl_df.index.get_indexer([walcl_df.index[-1] - pd.DateOffset(months=1)], method='nearest')[0]]) - 1) * 100

        return {
            "FED Funds Rate": f"{fed_funds:.2f}%", "US CPI (Inflación YoY)": f"{cpi_yoy:.2f}%",
            "US Unemployment Rate": f"{unrate:.1f}%", "FED Balance Sheet (MoM)": f"{walcl_mom:.2f}% ({"🟢 Inyectando" if walcl_mom > 0 else "🔴 Retirando"})"
        }
    except: return None

@st.cache_data(ttl=3600) 
def obtener_fundamentales(ticker):
    if ticker.startswith("^") or "=" in ticker or ticker in ["MERVAL_USD", "GSR"] or ("-" in ticker and ticker != "BTC-USD"): return {}
    try:
        info = yf.Ticker(ticker).info
        return {
            "PE": info.get("trailingPE", "-"),
            "Fwd P/E": info.get("forwardPE", "-"), # MÉTRICA FUTURA AÑADIDA
            "Beta": info.get("beta", "-"), 
            "Target": info.get("targetMeanPrice", "-"),
            "EPS": info.get("trailingEps", "-"), 
            "Rec": info.get("recommendationKey", "-").replace("_", " ").title()
        }
    except: return {}

@st.cache_data(ttl=3600)
def obtener_opciones_titanes(tickers_titanes):
    resultados = []
    for t in tickers_titanes:
        try:
            tk = yf.Ticker(t)
            if tk.options:
                opt = tk.option_chain(tk.options[0])
                p_oi = opt.puts['openInterest'].sum() if 'openInterest' in opt.puts else 0
                c_oi = opt.calls['openInterest'].sum() if 'openInterest' in opt.calls else 0
                if pd.isna(p_oi): p_oi = 0
                if pd.isna(c_oi): c_oi = 0
                resultados.append({
                    "Titan": t, "Put/Call Ratio": round(p_oi/c_oi, 2) if c_oi > 0 else 0,
                    "Puts (OI)": int(p_oi), "Calls (OI)": int(c_oi)
                })
        except: continue
    return pd.DataFrame(resultados)

# ==========================================
# BLOQUE 4: MOTOR MATEMÁTICO
# ==========================================
def calcular_metricas(df_precios, df_volumen, ticker, nombre, fecha_ref, fecha_u):
    fecha_p = pd.to_datetime(fecha_ref).normalize()
    serie_p = df_precios[ticker].loc[:fecha_p].dropna()
    if serie_p.empty: raise ValueError("Sin datos")
    precio_a = serie_p.iloc[-1]
    es_a = fecha_p >= pd.to_datetime(fecha_u).normalize()
    
    def format_pct(val): return f"{val:.2f}%" if pd.notnull(val) and isinstance(val, (int, float)) else "-"
    def pct_c(days):
        try: return ((precio_a - serie_p.iloc[-days]) / serie_p.iloc[-days]) * 100
        except: return "-"

    try: ytd = ((precio_a - serie_p.loc[serie_p.index.year == fecha_p.year].iloc[0]) / serie_p.loc[serie_p.index.year == fecha_p.year].iloc[0]) * 100
    except: ytd = "-"
    
    try: h52, l52 = f"{serie_p.iloc[-252:].max():.2f}", f"{serie_p.iloc[-252:].min():.2f}"
    except: h52, l52 = "-", "-"

    rsi_val, sma200_dist, mdd_val = "-", "-", "-"
    try:
        if len(serie_p) >= 15:
            delta = serie_p.diff()
            rs = delta.clip(lower=0).ewm(com=13, adjust=False).mean() / (-1 * delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
            rsi_val = f"{100 - (100 / (1 + rs)).iloc[-1]:.1f}"
        if len(serie_p) >= 200: sma200_dist = format_pct(((precio_a - serie_p.rolling(200).mean().iloc[-1]) / serie_p.rolling(200).mean().iloc[-1]) * 100)
        if len(serie_p.iloc[-252:]) > 0: mdd_val = format_pct(((serie_p.iloc[-252:] - serie_p.iloc[-252:].cummax()) / serie_p.iloc[-252:].cummax()).min() * 100)
    except: pass

    fund = obtener_fundamentales(ticker) if es_a else {}
    return {
        "Nombre": f'<a href="{get_tv_url(ticker)}" target="_blank" class="tv-link">{nombre}</a>', "Precio / Ratio": f"{precio_a:,.2f}", 
        "Low 52W": l52, "High 52W": h52,
        "1D": format_pct(pct_c(1)), "1W": format_pct(pct_c(5)), "1M": format_pct(pct_c(21)), 
        "YTD": format_pct(ytd), "1Y": format_pct(pct_c(252)), "3Y": format_pct(pct_c(756)),
        "RSI (14)": rsi_val, "SMA 200 Dist.": sma200_dist, "MDD 1Y": mdd_val,
        "P/E": f"{fund.get('PE'):.2f}" if isinstance(fund.get('PE'), (int,float)) else "-",
        "Fwd P/E": f"{fund.get('Fwd P/E'):.2f}" if isinstance(fund.get('Fwd P/E'), (int,float)) else "-",
        "Beta": f"{fund.get('Beta'):.2f}" if isinstance(fund.get('Beta'), (int,float)) else "-",
        "Target": f"{fund.get('Target'):.2f}" if isinstance(fund.get('Target'), (int,float)) else "-",
        "BPA": f"{fund.get('EPS'):.2f}" if isinstance(fund.get('EPS'), (int,float)) else "-", "Rec.": fund.get("Rec", "-")
    }

def generar_tabla_html_agrupada(df, clase_css):
    html = f'<div class="{clase_css}"><table>'
    html += '''
    <thead>
        <tr>
            <th class="group-header">IDENTIFICACIÓN</th>
            <th colspan="3" class="group-header">PRECIOS & RANGO</th>
            <th colspan="6" class="group-header">RENDIMIENTOS (%)</th>
            <th colspan="3" class="group-header">ANÁLISIS QUANT</th>
            <th colspan="6" class="group-header">FUNDAMENTALES</th>
        </tr>
        <tr>
            <th>Nombre</th>
            <th>Precio/Ratio</th><th>Low 52W</th><th>High 52W</th>
            <th>1D</th><th>1W</th><th>1M</th><th>YTD</th><th>1Y</th><th>3Y</th>
            <th>RSI (14)</th><th>SMA 200</th><th>MDD 1Y</th>
            <th>P/E</th><th>Fwd P/E</th><th>Beta</th><th>Target</th><th>BPA</th><th>Rec.</th>
        </tr>
    </thead>
    <tbody>
    '''
    for _, row in df.iterrows():
        html += "<tr>"
        columnas_ordenadas = ["Nombre", "Precio / Ratio", "Low 52W", "High 52W", "1D", "1W", "1M", "YTD", "1Y", "3Y", "RSI (14)", "SMA 200 Dist.", "MDD 1Y", "P/E", "Fwd P/E", "Beta", "Target", "BPA", "Rec."]
        for col in columnas_ordenadas:
            val = row.get(col, "-")
            if col in ["1D", "1W", "1M", "YTD", "1Y", "3Y", "SMA 200 Dist.", "MDD 1Y"]:
                style = color_heatmap(str(val))
                html += f'<td style="{style}">{val}</td>'
            else:
                html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

def color_heatmap(val):
    if isinstance(val, str) and "%" in val:
        try:
            num = float(val.replace("%", ""))
            if num > 3: c = '#1E7B1E' 
            elif num > 1: c = '#228B22' 
            elif num > 0: c = '#3CB371' 
            elif num < -3: c = '#8B0000' 
            elif num < -1: c = '#B22222' 
            elif num < 0: c = '#CD5C5C' 
            else: c = 'transparent'
            return f'background-color: {c}; color: white; border-radius: 4px;'
        except: return ''
    return ''

# ==========================================
# BLOQUE 5: INTERFAZ VISUAL (UI)
# ==========================================
col_title, col_cal = st.columns([2, 1])
df_p, df_v, hora_act = obtener_precios()

with col_title: 
    st.title("🛡️ Master Command")
    if hora_act: st.caption(f"Última lectura del mercado: **{hora_act}** (Hora del Servidor)")
        
with col_cal: 
    st.write("") 
    fecha_sel = st.date_input("🗓️ Fecha de Cálculo Histórico", value=date.today(), max_value=date.today())
    if st.button("🔄 Actualizar Datos Ahora"):
        st.cache_data.clear()
        st.rerun()

with st.spinner('Validando caché y procesando matemáticas en memoria...'):

    # TABLEROS PRINCIPALES
    if not df_p.empty:
        f_u = df_p.index[-1].date()
        for cat, items in ACTIVOS.items():
            st.subheader(cat)
            res = []
            for n, t in items.items():
                try: res.append(calcular_metricas(df_p, df_v, t, n, fecha_sel, f_u))
                except: continue
            
            if res:
                df_res = pd.DataFrame(res)
                clase_css = "titanes-scroll" if "TITANES" in cat else "table-container"
                html_table = generar_tabla_html_agrupada(df_res, clase_css)
                st.markdown(html_table, unsafe_allow_html=True)
            
            # Ubicar Buscador debajo de TITANES GLOBALES
            if cat == "TITANES GLOBALES (15)":
                st.markdown("---")
                st.subheader("🔍 Buscador Táctico de Tickers")
                # Crear columna pequeña (1/3) para el buscador
                col_busqueda, _ = st.columns([1, 2])
                with col_busqueda:
                    search_ticker = st.text_input("Introduce Ticker (ej: NVDA, BTC-USD):").upper().strip()
                
                if search_ticker:
                    with st.spinner(f"Analizando {search_ticker}..."):
                        try:
                            # Descarga individual blindada
                            tk = yf.Ticker(search_ticker)
                            hist = tk.history(period="10y")
                            if not hist.empty:
                                df_s_p = pd.DataFrame({search_ticker: hist['Close']})
                                df_s_v = pd.DataFrame({search_ticker: hist['Volume']})
                                
                                df_s_p.index = df_s_p.index.tz_localize(None).normalize()
                                df_s_v.index = df_s_v.index.tz_localize(None).normalize()

                                res_s = calcular_metricas(df_s_p, df_s_v, search_ticker, search_ticker, fecha_sel, date.today())
                                if res_s:
                                    html_busqueda = generar_tabla_html_agrupada(pd.DataFrame([res_s]), "table-container")
                                    st.markdown(html_busqueda, unsafe_allow_html=True)
                            else:
                                st.error("❌ Ticker no encontrado en Yahoo Finance.")
                        except Exception as e:
                            st.error("❌ Ticker no válido o error de red.")

        if fecha_sel >= f_u:
            st.markdown("---")
            
            # MOVIDO: Bloque Macro de la FED justo antes de correlación y sentimiento
            macro_data = obtener_macro_fred()
            if macro_data:
                st.subheader("🦅 Radar Macroeconómico y Liquidez (FRED)")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Tasa FED (Fed Funds)", macro_data["FED Funds Rate"])
                c2.metric("Inflación CPI (YoY)", macro_data["US CPI (Inflación YoY)"])
                c3.metric("Desempleo (EE.UU.)", macro_data["US Unemployment Rate"])
                c4.metric("Balance FED (Var. Mensual)", macro_data["FED Balance Sheet (MoM)"])
                st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.warning("⚠️ Los servidores de la FED (FRED) no respondieron a tiempo o están en mantenimiento. Los datos macroeconómicos están temporalmente ocultos.")
            
            col_opt, col_corr = st.columns([1, 1])
            with col_opt:
                st.subheader("🕸️ Matriz de Correlación Dinámica (1 Año)")
                try:
                    titanes_tickers = list(ACTIVOS["TITANES GLOBALES (15)"].values())
                    existentes = [t for t in titanes_tickers if t in df_p.columns]
                    corr_matrix = df_p[existentes].iloc[-252:].pct_change().dropna(how='all').corr()
                    nombres_cortos = {v: k.split(" ")[0] for k, v in ACTIVOS["TITANES GLOBALES (15)"].items()}
                    corr_matrix = corr_matrix.rename(columns=nombres_cortos, index=nombres_cortos)
                    html_corr = corr_matrix.style.background_gradient(cmap='coolwarm', axis=None, vmin=-1, vmax=1).format("{:.2f}").to_html()
                    st.markdown(f'<div class="table-container">{html_corr}</div>', unsafe_allow_html=True)
                except: st.info("Datos insuficientes para la matriz de stress testing.")

            with col_corr:
                st.subheader("🔥 Sentimiento (Opciones)")
                df_opt = obtener_opciones_titanes(list(ACTIVOS["TITANES GLOBALES (15)"].values()))
                if not df_opt.empty:
                    df_opt['Titan'] = df_opt['Titan'].map(lambda x: nombres_cortos.get(x, x))
                    st.markdown(f'<div class="table-container">{df_opt.to_html(index=False)}</div>', unsafe_allow_html=True)
                else: st.info("La API de Yahoo no reporta contratos abiertos en este momento (Fines de semana o festivos).")

# ==========================================
# BLOQUE 6: EQUIVALENCIAS Y GLOSARIO
# ==========================================
st.markdown("---")
st.subheader("🇪🇺 Diccionario Maestro de Equivalencias UCITS")

ucits_data = [
    {"Categoría": "MAJOR INDICES", "ETF (Ticker US)": "MSCI World (URTH)", "UCITS Recomendado": "IWDA.L / EUNL.DE"},
    {"Categoría": "MAJOR INDICES", "ETF (Ticker US)": "MSCI Emerging Markets (EEM)", "UCITS Recomendado": "EMIM.L / IS3N.DE"},
    {"Categoría": "MAJOR INDICES", "ETF (Ticker US)": "S&P 500 Equal Weight (RSP)", "UCITS Recomendado": "SPXW.L / XDEW.DE"},
    {"Categoría": "BONDS (US ETFs)", "ETF (Ticker US)": "US Treasury 0-1Y (SHV)", "UCITS Recomendado": "VDST.L / IB01.L"},
    {"Categoría": "BONDS (US ETFs)", "ETF (Ticker US)": "US Treasury 20Y+ (TLT)", "UCITS Recomendado": "DTLA.L / IDTL.L"},
    {"Categoría": "BONDS (US ETFs)", "ETF (Ticker US)": "Intl Gov Bonds (BNDX)", "UCITS Recomendado": "VETY.DE / IGLA.L"},
    {"Categoría": "GLOBAL FACTORS", "ETF (Ticker US)": "Large Cap Value (IVE)", "UCITS Recomendado": "CBUV.L / IUSV.DE"},
    {"Categoría": "GLOBAL FACTORS", "ETF (Ticker US)": "Large Cap Growth (IVW)", "UCITS Recomendado": "IUSG.DE / IWYG.L"},
    {"Categoría": "GLOBAL FACTORS", "ETF (Ticker US)": "Small Cap Value (IWN)", "UCITS Recomendado": "ZPRV.DE"},
    {"Categoría": "GLOBAL FACTORS", "ETF (Ticker US)": "Small Cap Growth (IWO)", "UCITS Recomendado": "IUSN.DE (General SC)"},
    {"Categoría": "GLOBAL FACTORS", "ETF (Ticker US)": "Value (VLUE)", "UCITS Recomendado": "IWVL.L"},
    {"Categoría": "GLOBAL FACTORS", "ETF (Ticker US)": "Quality (QUAL)", "UCITS Recomendado": "IWQU.L"},
    {"Categoría": "GLOBAL FACTORS", "ETF (Ticker US)": "Dividend (VYMI)", "UCITS Recomendado": "VHYL.L / VHYD.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Technology (XLK)", "UCITS Recomendado": "IUIT.L / QDVE.DE"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Healthcare (XLV)", "UCITS Recomendado": "IUHC.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Financials (XLF)", "UCITS Recomendado": "IUFS.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Cons Discretionary (XLY)", "UCITS Recomendado": "IUCD.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Communication (XLC)", "UCITS Recomendado": "CMTC.L / IUCM.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Industrials (XLI)", "UCITS Recomendado": "IUDS.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Cons Staples (XLP)", "UCITS Recomendado": "IUCG.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Energy (XLE)", "UCITS Recomendado": "IUES.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Utilities (XLU)", "UCITS Recomendado": "IUUS.L"},
    {"Categoría": "US SECTORS", "ETF (Ticker US)": "Real Estate (XLRE)", "UCITS Recomendado": "IUSP.L"},
    {"Categoría": "ASIA & LATAM", "ETF (Ticker US)": "Japan (EWJ)", "UCITS Recomendado": "IJPN.L"},
    {"Categoría": "ASIA & LATAM", "ETF (Ticker US)": "South Korea (EWY)", "UCITS Recomendado": "CSKR.L"},
    {"Categoría": "ASIA & LATAM", "ETF (Ticker US)": "India (INDA)", "UCITS Recomendado": "NDIA.L / IIND.L"},
    {"Categoría": "ASIA & LATAM", "ETF (Ticker US)": "China (MCHI)", "UCITS Recomendado": "HMCH.L / ICHN.L"},
    {"Categoría": "ASIA & LATAM", "ETF (Ticker US)": "Brazil (EWZ)", "UCITS Recomendado": "IBZL.AS / IBZL.L"},
    {"Categoría": "ASIA & LATAM", "ETF (Ticker US)": "Mexico (EWW)", "UCITS Recomendado": "CMX1.DE"}
]

ucits_df = pd.DataFrame(ucits_data)
st.markdown(f'<div class="table-container">{ucits_df.to_html(index=False)}</div>', unsafe_allow_html=True)

st.info("""
### 📚 Manual de Interpretación Analítica Avanzada
Este tablero no solo monitoriza el mercado, sino que evalúa la salud estructural, el sentimiento oculto y los riesgos asimétricos de la cartera basándose en modelos cuantitativos.

#### 1. Posicionamiento Macro y Liquidez (El Motor del Mercado)
* **Balance de la FED (Liquidez):** Es la variable más correlacionada con los mercados alcistas desde 2008. Si la variación es **Verde (+)**, hay nueva liquidez entrando al sistema; el dinero buscará riesgo (Acciones, Bitcoin). Si es **Rojo (-)**, el entorno es restrictivo y los rebotes del mercado suelen ser frágiles.
* **Gold/Silver Ratio (GSR):** Ratio de aversión al riesgo global. Un valor **superior a 80** indica estrés financiero severo o deflación (el capital huye hacia la seguridad del oro). Un valor **inferior a 60** señala crecimiento económico, inflación industrial y apetito por el riesgo (la plata se encarece).

#### 2. Análisis Táctico e Indicadores Cuantitativos
* **RSI (Índice de Fuerza Relativa a 14 Días):** Mide la sobreextensión direccional del precio.
* *> 70 (Sobrecompra):* Euforia de corto plazo. Vulnerable a correcciones técnicas inminentes.
* *< 30 (Sobreventa):* Pánico de corto plazo. Suele presentar zonas de entrada de alta probabilidad estadística (rebote técnico).
* **SMA 200 Dist. (Distancia a la Media Móvil 200):** La gravedad del mercado. Si un activo se desvía más de un +15% a +25% de su media móvil de 200 días, la "goma elástica" está al máximo de su capacidad. Comprar en estos niveles reduce drásticamente el ratio riesgo/beneficio.
* **MDD 1Y (Máximo Drawdown):** La caída más profunda desde el máximo relativo de los últimos 12 meses. Es el verdadero medidor del "Riesgo de Ruina". Permite dimensionar la volatilidad estructural de un activo para ajustar el tamaño de la posición.

#### 3. Dinámica Institucional (Opciones y Correlación)
* **Matriz de Correlación (1 Año):** Revela el grado de diversificación real. Valores superiores a **+0.85 (Rojo)** significan que posees el mismo factor de riesgo bajo diferentes nombres. Valores **Negativos (Azul)** actúan como anclas estabilizadoras de la volatilidad del portafolio.
* **Sentimiento de Opciones (Put/Call Ratio):** Mide las apuestas direccionales del capital institucional.
    * *Lectura Clásica:* Un ratio > 1.0 implica más Puts abiertas (miedo/cobertura bajista). Un ratio < 1.0 indica más Calls (apetito alcista).
    * *Lectura Contrarian (Gamma Squeeze):* Cuando el ratio Put/Call es extremadamente bajo (ej. 0.40) junto con un RSI elevado, los creadores de mercado (Market Makers) están sobrecargados; la estructura está madura para un barrido de liquidez violento a la baja.
""")