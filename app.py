import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA Y DISEÑO VISUAL AVANZADO ---
st.set_page_config(layout="wide", page_title="Master Command by PS")

# Inyección de CSS para diseño de terminal profesional, scroll horizontal y congelamiento de columnas
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1 { text-align: right; }
    
    /* Contenedor que permite el scroll horizontal pero elimina el vertical */
    .table-container {
        width: 100%;
        overflow-x: auto;
        overflow-y: hidden;
        margin-bottom: 2rem;
        border-radius: 5px;
    }
    
    /* Diseño base de la tabla HTML */
    .table-container table {
        width: 100%;
        border-collapse: collapse;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
    }
    
    /* Celdas generales */
    .table-container th, .table-container td {
        padding: 10px 14px;
        text-align: center;
        border-bottom: 1px solid #262730;
        white-space: nowrap;
    }
    
    /* Fila de Títulos (Headers) */
    .table-container th {
        background-color: #1E1E24;
        color: #FFFFFF;
        font-weight: 600;
        border-bottom: 2px solid #333333;
    }
    
    /* MAGIA VISUAL: Congelar la primera columna (Nombre) */
    .table-container th:first-child, .table-container td:first-child {
        position: sticky;
        left: 0;
        background-color: #0E1117; /* Mismo color del fondo principal para ocultar lo que pasa por debajo */
        z-index: 2; /* Lo pone una capa por encima de las otras columnas */
        text-align: left;
        border-right: 1px solid #333333; /* Línea separadora sutil */
        font-weight: bold;
    }
    
    /* El título de la primera columna necesita estar una capa aún más arriba */
    .table-container th:first-child {
        background-color: #1E1E24;
        z-index: 3;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BLOQUE 1: DICCIONARIO MAESTRO ORDENADO ---
ACTIVOS = {
    "MAJOR INDICES": {
        "S&P 500 (^GSPC)": "^GSPC",
        "MSCI World (URTH)": "URTH", 
        "NASDAQ 100 (^NDX)": "^NDX",
        "Euro Stoxx 50 (^STOXX50E)": "^STOXX50E",
        "MSCI Emerging Markets (EEM)": "EEM", 
        "Russell 2000 (^RUT)": "^RUT",
        "S&P 500 Equal Weight (RSP)": "RSP",
        "VIX Volatility (^VIX)": "^VIX"
    },
    "TITANES GLOBALES (15)": {
        "Apple (AAPL)": "AAPL", "Microsoft (MSFT)": "MSFT", "Alphabet (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN", "NVIDIA (NVDA)": "NVDA", "Meta Platforms (META)": "META",
        "Tesla (TSLA)": "TSLA", "Berkshire Hathaway (BRK-B)": "BRK-B", "Eli Lilly (LLY)": "LLY",
        "JPMorgan Chase (JPM)": "JPM", "Visa (V)": "V", "Broadcom (AVGO)": "AVGO",
        "Novo Nordisk (NVO)": "NVO", "LVMH (LVMUY)": "LVMUY", "ASML (ASML)": "ASML" 
    },
    "CURRENCIES": {
        "EUR / USD (EURUSD=X)": "EURUSD=X",
        "EUR / GBP (EURGBP=X)": "EURGBP=X",
        "EUR / JPY (EURJPY=X)": "EURJPY=X",
        "USD / EUR (USDEUR=X)": "USDEUR=X",
        "USD / GBP (USDGBP=X)": "USDGBP=X",
        "USD / JPY (USDJPY=X)": "USDJPY=X"
    },
    "US TREASURY YIELD CURVE (Tasas %)": {
        "13-Week T-Bill (^IRX)": "^IRX",
        "5-Year T-Note (^FVX)": "^FVX",
        "10-Year T-Note (^TNX)": "^TNX",
        "30-Year T-Bond (^TYX)": "^TYX"
    },
    "BONDS (US ETFs - Precios)": {
        "US Treasury 0-1Y ETF (SHV)": "SHV",
        "US Treasury 20Y+ ETF (TLT)": "TLT",
        "Intl Gov Bonds ETF (BNDX)": "BNDX"
    },
    "COMMODITIES": {
        "Oil Brent (BZ=F)": "BZ=F", "Gold (GC=F)": "GC=F", "Silver (SI=F)": "SI=F",
        "Copper (HG=F)": "HG=F", "Soybeans (ZS=F)": "ZS=F", "Bitcoin (BTC-USD)": "BTC-USD"
    },
    "GLOBAL FACTORS (US ETFs)": {
        "Large Cap Value (IVE)": "IVE",
        "Large Cap Growth (IVW)": "IVW",
        "Small Cap Value (IWN)": "IWN",
        "Small Cap Growth (IWO)": "IWO",
        "Value (VLUE)": "VLUE", 
        "Quality (QUAL)": "QUAL", 
        "Dividend (VYMI)": "VYMI"
    },
    "US SECTORS (US ETFs)": {
        "Technology (XLK)": "XLK", "Healthcare (XLV)": "XLV", "Financials (XLF)": "XLF",
        "Cons Discretionary (XLY)": "XLY", "Communication (XLC)": "XLC", "Industrials (XLI)": "XLI",
        "Cons Staples (XLP)": "XLP", "Energy (XLE)": "XLE", "Utilities (XLU)": "XLU", "Real Estate (XLRE)": "XLRE"
    },
    "EUROPE": {
        "UK FTSE 100 (^FTSE)": "^FTSE", "France CAC 40 (^FCHI)": "^FCHI",
        "Germany DAX (^GDAXI)": "^GDAXI", "Netherlands AEX (^AEX)": "^AEX",
        "Spain IBEX 35 (^IBEX)": "^IBEX", "Italy FTSE MIB (FTSEMIB.MI)": "FTSEMIB.MI"
    },
    "ASIA & LATAM (US ETFs)": {
        "Japan (EWJ)": "EWJ", "South Korea (EWY)": "EWY", "India (INDA)": "INDA",
        "China (MCHI)": "MCHI", "Brazil (EWZ)": "EWZ", "Mexico (EWW)": "EWW",
        "Argentina Merval CCL (MERVAL_USD)": "MERVAL_USD" 
    }
}

TICKERS_AUXILIARES = ["^MERV", "GGAL.BA", "GGAL"]

# --- BLOQUE 2: MOTOR DE DATOS ---
@st.cache_data(ttl=300) 
def obtener_precios():
    all_tickers = []
    for categoria in ACTIVOS.values():
        all_tickers.extend(list(categoria.values()))
    if "MERVAL_USD" in all_tickers: all_tickers.remove("MERVAL_USD")
    all_tickers.extend(TICKERS_AUXILIARES)
    all_tickers = list(set(all_tickers)) 
    
    try:
        data = yf.download(all_tickers, period="10y", interval="1d", auto_adjust=False)
        
        if isinstance(data.columns, pd.MultiIndex):
            df_precios = data['Adj Close'] if 'Adj Close' in data.columns.levels[0] else data['Close']
            df_volumen = data['Volume']
        else:
            df_precios = data
            df_volumen = pd.DataFrame()
            
        df_precios.index = pd.to_datetime(df_precios.index).tz_localize(None).normalize()
        if not df_volumen.empty:
            df_volumen.index = pd.to_datetime(df_volumen.index).tz_localize(None).normalize()
        
        merv = df_precios['^MERV'].ffill()
        ggal_ba = df_precios['GGAL.BA'].ffill() 
        ggal_us = df_precios['GGAL'].ffill()    
        
        ccl = ggal_ba / (ggal_us * 10)
        df_precios['MERVAL_USD'] = merv / ccl
        
        return df_precios, df_volumen
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600) 
def obtener_fundamentales(ticker):
    if ticker.startswith("^") or "=" in ticker or ticker == "MERVAL_USD" or ("-" in ticker and ticker != "BTC-USD"):
        return {}
    try:
        info = yf.Ticker(ticker).info
        return {
            "PE": info.get("trailingPE", "-"),
            "Beta": info.get("beta", "-"),
            "Target": info.get("targetMeanPrice", "-"),
            "EPS": info.get("trailingEps", "-"),
            "Rec": info.get("recommendationKey", "-").replace("_", " ").title()
        }
    except:
        return {}

@st.cache_data(ttl=3600)
def obtener_opciones_titanes(tickers_titanes):
    resultados = []
    for ticker in tickers_titanes:
        try:
            tk = yf.Ticker(ticker)
            expirations = tk.options
            if expirations:
                opt = tk.option_chain(expirations[0])
                puts_oi = opt.puts['openInterest'].sum()
                calls_oi = opt.calls['openInterest'].sum()
                vol_puts = opt.puts['volume'].sum()
                vol_calls = opt.calls['volume'].sum()
                
                ratio_oi = puts_oi / calls_oi if calls_oi > 0 else 0
                
                resultados.append({
                    "Titan": ticker,
                    "Vencimiento": expirations[0],
                    "Put/Call Ratio": round(ratio_oi, 2),
                    "Puts (Open Interest)": int(puts_oi) if pd.notna(puts_oi) else 0,
                    "Calls (Open Interest)": int(calls_oi) if pd.notna(calls_oi) else 0,
                    "Total Puts (Vol)": int(vol_puts) if pd.notna(vol_puts) else 0,
                    "Total Calls (Vol)": int(vol_calls) if pd.notna(vol_calls) else 0
                })
        except:
            continue
    return pd.DataFrame(resultados)

# --- BLOQUE 3: CÁLCULO DE MÉTRICAS ---
def calcular_metricas(df_precios, df_volumen, ticker, nombre, fecha_ref, fecha_ultima_cotizacion):
    if ticker not in df_precios.columns: raise ValueError("Sin datos")

    fecha_pandas = pd.to_datetime(fecha_ref).normalize()
    serie_precios = df_precios[ticker].loc[:fecha_pandas].dropna()
    
    if serie_precios.empty: raise ValueError("Sin datos")
    precio_actual = serie_precios.iloc[-1]
    
    es_actual = fecha_pandas >= pd.to_datetime(fecha_ultima_cotizacion).normalize()
    
    def format_pct(val):
        return f"{val:.2f}%" if isinstance(val, (int, float)) else "-"
    
    def pct_change(days):
        try:
            inicio = serie_precios.iloc[-days]
            return ((precio_actual - inicio) / inicio) * 100
        except: return "-"

    try:
        inicio_anio = serie_precios.loc[serie_precios.index.year == fecha_pandas.year].iloc[0]
        ytd = ((precio_actual - inicio_anio) / inicio_anio) * 100
    except: ytd = "-"
    
    try:
        ultimo_anio = serie_precios.iloc[-252:]
        high_52w = f"{ultimo_anio.max():.2f}"
        low_52w = f"{ultimo_anio.min():.2f}"
    except:
        high_52w, low_52w = "-", "-"

    vol_pct_str = "-"
    if es_actual and not df_volumen.empty and ticker in df_volumen.columns:
        serie_vol = df_volumen[ticker].loc[:fecha_pandas].dropna()
        if len(serie_vol) >= 63: 
            vol_hoy = serie_vol.iloc[-1]
            vol_promedio_3m = serie_vol.iloc[-63:].mean()
            if vol_promedio_3m > 0:
                vol_pct = ((vol_hoy / vol_promedio_3m) - 1) * 100
                vol_pct_str = format_pct(vol_pct)

    fund = obtener_fundamentales(ticker) if es_actual else {}

    return {
        "Nombre": nombre,
        "Precio / Tasa": f"{precio_actual:,.2f}",
        "Low 52W": low_52w,
        "High 52W": high_52w,
        "1D": format_pct(pct_change(1)),
        "1W": format_pct(pct_change(5)),
        "1M": format_pct(pct_change(21)),
        "YTD": format_pct(ytd),
        "1Y": format_pct(pct_change(252)),
        "3Y": format_pct(pct_change(756)),
        "P/E": f"{fund.get('PE'):.2f}" if isinstance(fund.get("PE"), (int, float)) else fund.get("PE", "-"),
        "Beta": f"{fund.get('Beta'):.2f}" if isinstance(fund.get("Beta"), (int, float)) else fund.get("Beta", "-"),
        "Target P.": f"{fund.get('Target'):.2f}" if isinstance(fund.get("Target"), (int, float)) else fund.get("Target", "-"),
        "% Vol vs 3M": vol_pct_str,
        "BPA (TTM)": f"{fund.get('EPS'):.2f}" if isinstance(fund.get("EPS"), (int, float)) else fund.get("EPS", "-"),
        "Rec.": fund.get("Rec", "-")
    }

# --- BLOQUE 4: INTERFAZ MASTER COMMAND ---
col_cal, col_title = st.columns([1, 2])
with col_cal:
    fecha_seleccionada = st.date_input(
        "🗓️ Fecha de Cálculo", 
        value=date.today(), 
        max_value=date.today()
    )
with col_title:
    st.title("🛡️ Master Command by PS")

def color_heatmap(val):
    if isinstance(val, str) and "%" in val:
        try:
            num = float(val.replace("%", ""))
            if num > 3: color = '#1E7B1E' 
            elif num > 1: color = '#228B22' 
            elif num > 0: color = '#3CB371' 
            elif num < -3: color = '#8B0000' 
            elif num < -1: color = '#B22222' 
            elif num < 0: color = '#CD5C5C' 
            else: color = 'transparent'
            return f'background-color: {color}; color: white; border-radius: 4px;'
        except: return ''
    return ''

with st.spinner('Consolidando datos de mercado, opciones y fundamentales...'):
    df_precios, df_volumen = obtener_precios()
    
    if df_precios.empty:
        st.error("🚨 Error de conexión con el proveedor de datos. Los servidores de Yahoo pueden estar saturados.")
    else:
        fecha_ultima_cotizacion = df_precios.index[-1].date()
        
        for categoria, items in ACTIVOS.items():
            st.subheader(categoria)
            lista_resultados = []
            
            for nombre, ticker in items.items():
                try:
                    metrica = calcular_metricas(df_precios, df_volumen, ticker, nombre, fecha_seleccionada, fecha_ultima_cotizacion)
                    lista_resultados.append(metrica)
                except: continue
            
            if lista_resultados:
                df_display = pd.DataFrame(lista_resultados)
                
                # Renderizado HTML puro para lograr el efecto Sticky Column y evitar Scroll Vertical
                styled_html = df_display.style.map(color_heatmap, subset=['1D', '1W', '1M', 'YTD', '1Y', '3Y']).hide(axis="index").to_html()
                st.markdown(f'<div class="table-container">{styled_html}</div>', unsafe_allow_html=True)

        # MÓDULO DE POSICIÓN ABIERTA
        es_actual_global = pd.to_datetime(fecha_seleccionada).date() >= fecha_ultima_cotizacion
        if es_actual_global:
            st.markdown("---")
            st.subheader("🔥 Sentimiento Institucional Opciones (Titanes Globales)")
            st.caption("Ratio mayor a 1.0 = Sentimiento Bajista/Cobertura. Menor a 1.0 = Sentimiento Alcista. Columnas Open Interest detallan contratos abiertos.")
            
            tickers_titanes = list(ACTIVOS["TITANES GLOBALES (15)"].values())
            df_opciones = obtener_opciones_titanes(tickers_titanes)
            if not df_opciones.empty:
                # Renderizado HTML puro
                html_opciones = df_opciones.style.hide(axis="index").to_html()
                st.markdown(f'<div class="table-container">{html_opciones}</div>', unsafe_allow_html=True)
            else:
                st.info("Datos de cadena de opciones no disponibles temporalmente en la API (Común en fines de semana por mantenimiento).")

# --- BLOQUE 5: TABLA DE EQUIVALENCIAS UCITS ---
st.markdown("---")
st.subheader("🇪🇺 Diccionario de Equivalencias: US ETFs a UCITS (Europa)")
ucits_data = {
    "Exposición / Ticker US": [
        "MSCI World (URTH)", "Emerging Markets (EEM)", "S&P 500 Equal Weight (RSP)", 
        "US Treasury 20Y+ (TLT)", "US Treasury 0-1Y (SHV)", "Intl Gov Bonds (BNDX)",
        "Large Cap Value (IVE)", "Large Cap Growth (IVW)", "Small Cap Value (IWN)", 
        "Small Cap Growth (IWO)", "Value Factor (VLUE)", "Quality Factor (QUAL)", "Dividend Factor (VYMI)",
        "Technology (XLK)", "Healthcare (XLV)", "Financials (XLF)", "Cons Discretionary (XLY)",
        "Communication (XLC)", "Industrials (XLI)", "Cons Staples (XLP)", "Energy (XLE)", 
        "Utilities (XLU)", "Real Estate (XLRE)", "Japan (EWJ)", "South Korea (EWY)", 
        "India (INDA)", "China (MCHI)", "Brazil (EWZ)", "Mexico (EWW)"
    ],
    "UCITS Recomendado (Ticker Europa)": [
        "IWDA.L / EUNL.DE", "EMIM.L", "SPXW.L / XDEW.DE", 
        "DTLA.L", "VDST.L", "VETY.DE",
        "CBUV.L", "IUSG.DE", "ZPRV.DE", 
        "IUSN.DE (General SC)", "IWVL.L", "IWQU.L", "VHYL.L",
        "IUIT.L", "IUHC.L", "IUFS.L", "IUCD.L",
        "CMTC.L", "IUDS.L", "IUCG.L", "IUES.L", 
        "IUUS.L", "IUSP.L", "IJPN.L", "CSKR.L", 
        "NDIA.L", "HMCH.L", "IBZL.AS", "CMX1.DE"
    ]
}
# Renderizado HTML puro
html_ucits = pd.DataFrame(ucits_data).style.hide(axis="index").to_html()
st.markdown(f'<div class="table-container">{html_ucits}</div>', unsafe_allow_html=True)