import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
import re

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS ---
st.set_page_config(layout="wide", page_title="Master Command by PS")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1 { text-align: right; }
    
    .table-container {
        width: 100%;
        overflow-x: auto;
        overflow-y: visible;
        margin-bottom: 3rem;
    }
    
    .table-container table {
        width: 100%;
        border-collapse: separate; 
        border-spacing: 0;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
    }

    .table-container th {
        position: sticky;
        top: 0;
        background-color: #1E1E24;
        color: #FFFFFF;
        z-index: 10;
        padding: 12px;
        border-bottom: 2px solid #333333;
        white-space: nowrap;
    }

    .table-container td {
        padding: 10px 14px;
        text-align: center;
        border-bottom: 1px solid #262730;
        white-space: nowrap;
        background-color: #0E1117;
    }

    .table-container td:first-child, .table-container th:first-child {
        position: sticky;
        left: 0;
        z-index: 11;
        text-align: left;
        border-right: 2px solid #333333;
    }
    
    .table-container td:first-child {
        background-color: #161a21; 
    }

    .table-container th:first-child {
        z-index: 12;
        background-color: #1E1E24;
    }

    .tv-link {
        color: #2962FF;
        text-decoration: none;
        font-weight: bold;
    }
    .tv-link:hover {
        text-decoration: underline;
        color: #448AFF;
    }
    
    div[data-testid="metric-container"] {
        background-color: #161a21;
        border: 1px solid #333333;
        padding: 15px;
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

# --- BLOQUE 2: LÓGICA DE TRADINGVIEW CORREGIDA ---
def get_tv_url(ticker):
    # Traducción manual para evitar errores de limpieza de texto
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
        # Limpieza selectiva para no romper tickers con X o F
        symbol = ticker.replace('=X', '').replace('=F', '').replace('-', '').replace('^', '')
        
    return f"https://www.tradingview.com/chart/?symbol={symbol}"

# --- BLOQUE 3: MOTOR DE DATOS ---
@st.cache_data(ttl=300) 
def obtener_precios():
    all_tickers = []
    for cat in ACTIVOS.values(): all_tickers.extend(list(cat.values()))
    # Excluimos sintéticos de la descarga directa
    tickers_descarga = [t for t in all_tickers if t not in ["MERVAL_USD", "GSR"]]
    tickers_descarga.extend(TICKERS_AUXILIARES)
    tickers_descarga = list(set(tickers_descarga)) 
    
    try:
        data = yf.download(tickers_descarga, period="10y", interval="1d", auto_adjust=False)
        if isinstance(data.columns, pd.MultiIndex):
            df_precios = data['Adj Close'] if 'Adj Close' in data.columns.levels[0] else data['Close']
            df_volumen = data['Volume']
        else:
            df_precios, df_volumen = data, pd.DataFrame()
            
        df_precios.index = pd.to_datetime(df_precios.index).tz_localize(None).normalize()
        if not df_volumen.empty:
            df_volumen.index = pd.to_datetime(df_volumen.index).tz_localize(None).normalize()
        
        # CCL Argentina
        merv, ggal_ba, ggal_us = df_precios['^MERV'].ffill(), df_precios['GGAL.BA'].ffill(), df_precios['GGAL'].ffill()    
        df_precios['MERVAL_USD'] = merv / (ggal_ba / (ggal_us * 10))
        
        # GSR (Gold/Silver Ratio) Sintético
        if 'GC=F' in df_precios.columns and 'SI=F' in df_precios.columns:
            df_precios['GSR'] = df_precios['GC=F'].ffill() / df_precios['SI=F'].ffill()
            
        return df_precios, df_volumen
    except: return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600)
def obtener_macro_fred():
    try:
        def fetch_fred(series_id):
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
            df = pd.read_csv(url, index_col='DATE', parse_dates=True)
            df.columns = [series_id]
            df[series_id] = pd.to_numeric(df[series_id], errors='coerce')
            return df.dropna()

        fed_df, cpi_df, unrate_df, walcl_df = fetch_fred('FEDFUNDS'), fetch_fred('CPIAUCSL'), fetch_fred('UNRATE'), fetch_fred('WALCL')
        
        cpi_latest = cpi_df['CPIAUCSL'].iloc[-1]
        cpi_idx = cpi_df.index.get_indexer([cpi_df.index[-1] - pd.DateOffset(years=1)], method='nearest')[0]
        cpi_yoy = ((cpi_latest / cpi_df['CPIAUCSL'].iloc[cpi_idx]) - 1) * 100

        walcl_latest = walcl_df['WALCL'].iloc[-1]
        walcl_idx = walcl_df.index.get_indexer([walcl_df.index[-1] - pd.DateOffset(months=1)], method='nearest')[0]
        walcl_mom = ((walcl_latest / walcl_df['WALCL'].iloc[walcl_idx]) - 1) * 100

        return {
            "FED Funds Rate": f"{fed_df['FEDFUNDS'].iloc[-1]:.2f}%",
            "US CPI (Inflación YoY)": f"{cpi_yoy:.2f}%",
            "US Unemployment Rate": f"{unrate_df['UNRATE'].iloc[-1]:.1f}%",
            "FED Balance Sheet (MoM)": f"{walcl_mom:.2f}% ({"🟢 Inyectando" if walcl_mom > 0 else "🔴 Retirando"})"
        }
    except: return None

@st.cache_data(ttl=3600) 
def obtener_fundamentales(ticker):
    if ticker.startswith("^") or "=" in ticker or ticker in ["MERVAL_USD", "GSR"] or ("-" in ticker and ticker != "BTC-USD"): return {}
    try:
        info = yf.Ticker(ticker).info
        return {
            "PE": info.get("trailingPE", "-"), "Beta": info.get("beta", "-"), "Target": info.get("targetMeanPrice", "-"),
            "EPS": info.get("trailingEps", "-"), "Rec": info.get("recommendationKey", "-").replace("_", " ").title()
        }
    except: return {}

@st.cache_data(ttl=3600)
def obtener_opciones_titanes(tickers_titanes):
    resultados = []
    for t in tickers_titanes:
        try:
            tk = yf.Ticker(t)
            exp = tk.options
            if exp:
                opt = tk.option_chain(exp[0])
                p_oi, c_oi = opt.puts['openInterest'].sum(), opt.calls['openInterest'].sum()
                v_p, v_c = opt.puts['volume'].sum(), opt.calls['volume'].sum()
                resultados.append({
                    "Titan": t, "Vencimiento": exp[0], "Put/Call Ratio": round(p_oi/c_oi, 2) if c_oi>0 else 0,
                    "Puts (OI)": int(p_oi), "Calls (OI)": int(c_oi), "Puts (Vol)": int(v_p), "Calls (Vol)": int(v_c)
                })
        except: continue
    return pd.DataFrame(resultados)

# --- BLOQUE 4: CÁLCULO DE MÉTRICAS ---
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

    vol_pct = "-"
    if es_a and not df_volumen.empty and ticker in df_volumen.columns:
        s_vol = df_volumen[ticker].loc[:fecha_p].dropna()
        if len(s_vol) >= 63 and s_vol.iloc[-63:].mean() > 0: 
            vol_pct = format_pct(((s_vol.iloc[-1] / s_vol.iloc[-63:].mean()) - 1) * 100)

    rsi_val, sma200_dist, mdd_val = "-", "-", "-"
    try:
        if len(serie_p) >= 15:
            delta = serie_p.diff()
            rs = delta.clip(lower=0).ewm(com=13, adjust=False).mean() / (-1 * delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
            rsi_val = f"{100 - (100 / (1 + rs)).iloc[-1]:.1f}"
        if len(serie_p) >= 200: sma200_dist = format_pct(((precio_a - serie_p.rolling(window=200).mean().iloc[-1]) / serie_p.rolling(window=200).mean().iloc[-1]) * 100)
        if len(serie_p.iloc[-252:]) > 0: mdd_val = format_pct(((serie_p.iloc[-252:] - serie_p.iloc[-252:].cummax()) / serie_p.iloc[-252:].cummax()).min() * 100)
    except: pass

    fund = obtener_fundamentales(ticker) if es_a else {}
    return {
        "Nombre": f'<a href="{get_tv_url(ticker)}" target="_blank" class="tv-link">{nombre}</a>', 
        "Precio / Ratio": f"{precio_a:,.2f}", "1D": format_pct(pct_c(1)), "1W": format_pct(pct_c(5)), 
        "1M": format_pct(pct_c(21)), "YTD": format_pct(ytd), "1Y": format_pct(pct_c(252)), "3Y": format_pct(pct_c(756)),
        "RSI (14)": rsi_val, "SMA 200 Dist.": sma200_dist, "MDD 1Y": mdd_val, "Low 52W": l52, "High 52W": h52,
        "P/E": f"{fund.get('PE'):.2f}" if isinstance(fund.get('PE'), (int,float)) else "-",
        "Beta": f"{fund.get('Beta'):.2f}" if isinstance(fund.get('Beta'), (int,float)) else "-",
        "Target": f"{fund.get('Target'):.2f}" if isinstance(fund.get('Target'), (int,float)) else "-",
        "Vol vs 3M": vol_pct, "BPA": f"{fund.get('EPS'):.2f}" if isinstance(fund.get('EPS'), (int,float)) else "-", "Rec.": fund.get("Rec", "-")
    }

# --- BLOQUE 5: INTERFAZ ---
c_cal, c_tit = st.columns([1, 2])
with c_cal: fecha_sel = st.date_input("🗓️ Fecha de Cálculo", value=date.today(), max_value=date.today())
with c_tit: st.title("🛡️ Master Command by PS")

def color_h(val):
    if isinstance(val, str) and "%" in val:
        try:
            n = float(val.replace("%", ""))
            if n > 3: c = '#1E7B1E'
            elif n > 0: c = '#3CB371'
            elif n < -3: c = '#8B0000'
            elif n < 0: c = '#CD5C5C'
            else: c = 'transparent'
            return f'background-color: {c}; color: white; border-radius: 4px;'
        except: return ''
    return ''

with st.spinner('Actualizando algoritmos institucional...'):
    df_p, df_v = obtener_precios()
    macro = obtener_macro_fred()

    if macro:
        st.subheader("🦅 Radar Macro y Liquidez (FRED)")
        cols = st.columns(4)
        for i, (k, v) in enumerate(macro.items()): cols[i].metric(k, v)

    if not df_p.empty:
        f_u = df_p.index[-1].date()
        for cat, items in ACTIVOS.items():
            st.subheader(cat)
            res = []
            for n, t in items.items():
                try: res.append(calcular_metricas(df_p, df_v, t, n, fecha_sel, f_u))
                except: continue
            if res:
                df_r = pd.DataFrame(res)
                st.markdown(f'<div class="table-container">{df_r.style.map(color_h, subset=['1D', '1W', '1M', 'YTD', '1Y', '3Y', 'SMA 200 Dist.', 'MDD 1Y']).hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        if fecha_sel >= f_u:
            st.markdown("---")
            c_opt, c_corr = st.columns([1, 1])
            with c_opt:
                st.subheader("🕸️ Matriz de Correlación (1 Año)")
                try:
                    titanes = list(ACTIVOS["TITANES GLOBALES (15)"].values())
                    # FILTRADO BLINDADO: Solo tickers que existan en la descarga
                    existentes = [t for t in titanes if t in df_p.columns]
                    if len(existentes) > 1:
                        corr = df_p[existentes].iloc[-252:].pct_change().corr()
                        mapa = {v: k.split(" ")[0] for k, v in ACTIVOS["TITANES GLOBALES (15)"].items()}
                        corr = corr.rename(columns=mapa, index=mapa)
                        st.markdown(f'<div class="table-container">{corr.style.background_gradient(cmap='coolwarm', axis=None, vmin=-1, vmax=1).format("{:.2f}").to_html()}</div>', unsafe_allow_html=True)
                    else: st.info("Datos insuficientes para la matriz.")
                except: st.info("Error al procesar la matriz.")
            with c_corr:
                st.subheader("🔥 Sentimiento Opciones")
                df_o = obtener_opciones_titanes(list(ACTIVOS["TITANES GLOBALES (15)"].values()))
                if not df_o.empty:
                    n_map = {v: k.split(" ")[0] for k, v in ACTIVOS["TITANES GLOBALES (15)"].items()}
                    df_o['Titan'] = df_o['Titan'].map(n_map)
                    st.markdown(f'<div class="table-container">{df_o.to_html(index=False)}</div>', unsafe_allow_html=True)
                else: st.info("Datos de opciones no disponibles.")

# --- BLOQUE 6: EQUIVALENCIAS Y GLOSARIO ---
st.markdown("---")
st.subheader("🇪🇺 US ETFs a UCITS")
ucits_df = pd.DataFrame({
    "Ticker US": ["URTH", "EEM", "RSP", "TLT", "SHV", "XLK", "XLV", "IVE", "IVW", "IWN", "IWO"],
    "UCITS": ["IWDA.L", "EMIM.L", "SPXW.L", "DTLA.L", "VDST.L", "IUIT.L", "IUHC.L", "CBUV.L", "IUSG.DE", "ZPRV.DE", "IUSN.DE"]
})
st.markdown(f'<div class="table-container">{ucits_df.to_html(index=False)}</div>', unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #1E1E24; padding: 20px; border-radius: 8px; border-left: 5px solid #2962FF; margin-top: 20px;">
    <h4>📚 Manual de Interpretación Quant, Macro & GSR</h4>
    <ul>
        <li><b>Gold/Silver Ratio (GSR):</b> Indica cuántas onzas de plata se necesitan para comprar una de oro. 
            <ul>
                <li><i>GSR > 80:</i> Históricamente indica pánico o recesión. El oro está "caro" frente a la plata.</li>
                <li><i>GSR < 50:</i> Indica euforia económica o alta inflación industrial. La plata está fuerte.</li>
            </ul>
        </li>
        <li><b>RSI (14):</b> Sobrecomprado (>70) = Riesgo de caída. Sobrevendido (<30) = Oportunidad de rebote.</li>
        <li><b>Matriz de Correlación:</b> Rojo (+1) = Se mueven igual. Azul (-1) = Cobertura perfecta.</li>
    </ul>
</div>
""", unsafe_allow_html=True)