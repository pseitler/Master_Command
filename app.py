import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
import re

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS ---
st.set_page_config(layout="wide", page_title="Master Command by PS")

# CSS Profesional: Sticky Headers, Sticky Columns y Scroll Vertical para Titanes
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1 { text-align: right; }
    
    /* Contenedor General */
    .table-container {
        width: 100%;
        overflow-x: auto;
        margin-bottom: 2rem;
    }
    
    /* Contenedor Específico para Titanes (Con Scroll Vertical) */
    .titanes-scroll {
        max-height: 450px;
        overflow-y: auto;
        border: 1px solid #333;
        margin-bottom: 3rem;
    }
    
    .table-container table, .titanes-scroll table {
        width: 100%;
        border-collapse: separate; 
        border-spacing: 0;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }

    /* Cabeceras Congeladas (Sticky Header) */
    .table-container th, .titanes-scroll th {
        position: sticky;
        top: 0;
        background-color: #1E1E24;
        color: #FFFFFF;
        z-index: 10;
        padding: 10px;
        border-bottom: 2px solid #333;
        white-space: nowrap;
    }

    /* Primera Columna Congelada (Sticky Column) */
    .table-container td:first-child, .table-container th:first-child,
    .titanes-scroll td:first-child, .titanes-scroll th:first-child {
        position: sticky;
        left: 0;
        z-index: 11;
        text-align: left;
        border-right: 2px solid #333;
        background-color: #161a21;
    }

    /* Intersección Header-Columna */
    .table-container th:first-child, .titanes-scroll th:first-child {
        z-index: 12;
        background-color: #1E1E24;
    }

    .table-container td, .titanes-scroll td {
        padding: 8px 12px;
        text-align: center;
        border-bottom: 1px solid #262730;
        white-space: nowrap;
        background-color: #0E1117;
    }

    .tv-link {
        color: #2962FF;
        text-decoration: none;
        font-weight: bold;
    }
    
    div[data-testid="metric-container"] {
        background-color: #161a21;
        border: 1px solid #444;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BLOQUE 1: DICCIONARIO MAESTRO ---
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

# --- BLOQUE 2: LÓGICA DE TRADINGVIEW (MAPEO FIJO) ---
def get_tv_url(ticker):
    tv_mapping = {
        "^GSPC": "SPX", "^NDX": "NDX", "^DJI": "DJI", "^FTSE": "UKX", "^IBEX": "IBC",
        "^GDAXI": "DAX", "^STOXX50E": "STOXX50", "^VIX": "VIX", 
        "^IRX": "US03MY", "^FVX": "US05Y", "^TNX": "US10Y", "^TYX": "US30Y", "GSR": "XAUXAG"
    }
    if ticker in tv_mapping:
        symbol = tv_mapping[ticker]
    elif "MERVAL" in ticker:
        symbol = "MERV"
    else:
        symbol = ticker.replace('=X', '').replace('=F', '').replace('-', '').replace('^', '')
    return f"https://www.tradingview.com/chart/?symbol={symbol}"

# --- BLOQUE 3: MOTOR DE DATOS ---
@st.cache_data(ttl=300) 
def obtener_precios():
    all_tickers = []
    for cat in ACTIVOS.values(): all_tickers.extend(list(cat.values()))
    tickers_descarga = [t for t in all_tickers if t not in ["MERVAL_USD", "GSR"]]
    tickers_descarga.extend(TICKERS_AUXILIARES)
    
    try:
        data = yf.download(list(set(tickers_descarga)), period="10y", interval="1d", auto_adjust=False)
        df_precios = data['Adj Close'] if 'Adj Close' in data.columns.levels[0] else data['Close']
        df_volumen = data['Volume']
        df_precios.index = pd.to_datetime(df_precios.index).tz_localize(None).normalize()
        
        # Sintéticos
        merv, ggal_ba, ggal_us = df_precios['^MERV'].ffill(), df_precios['GGAL.BA'].ffill(), df_precios['GGAL'].ffill()    
        df_precios['MERVAL_USD'] = merv / (ggal_ba / (ggal_us * 10))
        if 'GC=F' in df_precios.columns and 'SI=F' in df_precios.columns:
            df_precios['GSR'] = df_precios['GC=F'].ffill() / df_precios['SI=F'].ffill()
            
        return df_precios, df_volumen
    except: return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600)
def obtener_macro_fred():
    try:
        def fetch_fred(s_id):
            return pd.read_csv(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s_id}", index_col='DATE', parse_dates=True)
        
        fed, cpi, unrate, walcl = fetch_fred('FEDFUNDS'), fetch_fred('CPIAUCSL'), fetch_fred('UNRATE'), fetch_fred('WALCL')
        cpi_yoy = ((cpi.iloc[-1] / cpi.iloc[-13]) - 1) * 100
        walcl_mom = ((walcl.iloc[-1] / walcl.iloc[-5]) - 1) * 100
        
        return {
            "FED Funds": f"{fed.iloc[-1].values[0]:.2f}%",
            "CPI YoY": f"{cpi_yoy.values[0]:.2f}%",
            "Unemployment": f"{unrate.iloc[-1].values[0]:.1f}%",
            "FED Balance MoM": f"{walcl_mom.values[0]:.2f}% ({"🟢" if walcl_mom.values[0] > 0 else "🔴"})"
        }
    except: return None

@st.cache_data(ttl=3600)
def obtener_opciones_titanes(tickers):
    res = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            if tk.options:
                opt = tk.option_chain(tk.options[0])
                p_oi, c_oi = opt.puts['openInterest'].sum(), opt.calls['openInterest'].sum()
                res.append({"Titan": t, "Put/Call Ratio": round(p_oi/c_oi, 2) if c_oi>0 else 0, "Puts (OI)": int(p_oi), "Calls (OI)": int(c_oi)})
        except: continue
    return pd.DataFrame(res)

# --- BLOQUE 4: CÁLCULO DE MÉTRICAS ---
def calcular_metricas(df_p, df_v, ticker, nombre, fecha_sel, fecha_u):
    f_p = pd.to_datetime(fecha_sel).normalize()
    serie = df_p[ticker].loc[:f_p].dropna()
    if serie.empty: raise ValueError
    p_a = serie.iloc[-1]
    es_a = f_p >= pd.to_datetime(fecha_u).normalize()
    
    def pct(d): 
        try: return ((p_a - serie.iloc[-d]) / serie.iloc[-d]) * 100
        except: return "-"
    
    # RSI, SMA, MDD
    rsi, sma, mdd = "-", "-", "-"
    if len(serie) >= 200:
        sma = f"{((p_a - serie.rolling(200).mean().iloc[-1]) / serie.rolling(200).mean().iloc[-1]) * 100:.2f}%"
    if len(serie) >= 15:
        delta = serie.diff(); up, down = delta.clip(lower=0), -delta.clip(upper=0)
        rs = up.ewm(13).mean() / down.ewm(13).mean()
        rsi = f"{100 - (100 / (1 + rs)).iloc[-1]:.1f}"
    if len(serie) > 0:
        mdd = f"{((serie.iloc[-252:] - serie.iloc[-252:].cummax()) / serie.iloc[-252:].cummax()).min() * 100:.2f}%"

    fund = {}
    if es_a and ticker not in ["GSR", "MERVAL_USD"] and not ticker.startswith("^"):
        try: fund = yf.Ticker(ticker).info
        except: pass

    return {
        "Nombre": f'<a href="{get_tv_url(ticker)}" target="_blank" class="tv-link">{nombre}</a>',
        "Precio": f"{p_a:,.2f}", "1D": f"{pct(2):.2f}%" if isinstance(pct(2), float) else "-", 
        "1W": f"{pct(5):.2f}%" if isinstance(pct(5), float) else "-", "1M": f"{pct(21):.2f}%" if isinstance(pct(21), float) else "-",
        "YTD": f"{((p_a - serie.loc[serie.index.year == f_p.year].iloc[0]) / serie.loc[serie_p.index.year == f_p.year].iloc[0]) * 100:.2f}%" if not serie.loc[serie.index.year == f_p.year].empty else "-",
        "RSI": rsi, "SMA200D": sma, "MDD": mdd,
        "P/E": f"{fund.get('trailingPE', '-'):.2f}" if isinstance(fund.get('trailingPE'), (int, float)) else "-",
        "Beta": f"{fund.get('beta', '-'):.2f}" if isinstance(fund.get('beta'), (int, float)) else "-",
        "Rec.": fund.get("recommendationKey", "-").title()
    }

# --- BLOQUE 5: INTERFAZ ---
c1, c2 = st.columns([1, 2])
with c1: f_sel = st.date_input("📅 Fecha", value=date.today(), max_value=date.today())
with c2: st.title("🛡️ Master Command by PS")

with st.spinner('Analizando mercados...'):
    df_p, df_v = obtener_precios()
    macro = obtener_macro_fred()
    if macro:
        cols = st.columns(4)
        for i, (k, v) in enumerate(macro.items()): cols[i].metric(k, v)

    if not df_p.empty:
        f_u = df_p.index[-1].date()
        for cat, items in ACTIVOS.items():
            st.subheader(cat)
            res = []
            for n, t in items.items():
                try: res.append(calcular_metricas(df_p, df_v, t, n, f_sel, f_u))
                except: continue
            
            if res:
                df_r = pd.DataFrame(res)
                # Aplicamos la clase de scroll solo a Titanes
                container_class = "titanes-scroll" if "TITANES" in cat else "table-container"
                html = df_r.style.hide(axis="index").to_html(escape=False)
                st.markdown(f'<div class="{container_class}">{html}</div>', unsafe_allow_html=True)

        if f_sel >= f_u:
            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🕸️ Correlación (1Y)")
                try:
                    tits = [v for k, v in ACTIVOS["TITANES GLOBALES (15)"].items() if v in df_p.columns]
                    # Limpiamos NaNs para que la matriz no falle
                    df_corr = df_p[tits].iloc[-252:].pct_change().dropna(how='all').corr()
                    if not df_corr.empty:
                        st.markdown(f'<div class="table-container">{df_corr.style.background_gradient(cmap="coolwarm").format("{:.2f}").to_html()}</div>', unsafe_allow_html=True)
                    else: st.warning("No hay datos suficientes para correlación hoy.")
                except: st.error("Error al procesar matriz.")
            with col_b:
                st.subheader("🔥 Sentimiento Opciones")
                df_o = obtener_opciones_titanes(list(ACTIVOS["TITANES GLOBALES (15)"].values()))
                if not df_o.empty: st.markdown(f'<div class="table-container">{df_o.to_html(index=False)}</div>', unsafe_allow_html=True)
                else: st.info("Datos de opciones cerrados por fin de semana.")

# --- BLOQUE 6: EQUIVALENCIAS ---
st.markdown("---")
st.subheader("🇪🇺 US ETFs a UCITS")
st.table(pd.DataFrame({"US": ["URTH", "EEM", "TLT", "XLK", "XLV"], "UCITS": ["IWDA.L", "EMIM.L", "DTLA.L", "IUIT.L", "IUHC.L"]}))