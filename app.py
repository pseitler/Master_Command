import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Master Command by PS")

# --- ESTILOS CSS PROFESIONALES (MODO OSCURO Y TERMINAL) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    div[data-testid="stDataFrame"] { border: none; }
    .st-emotion-cache-16idsys p { font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- BLOQUE 1: DICCIONARIO MAESTRO (ETFs US e Índices Puros) ---
ACTIVOS = {
    "MAJOR INDICES": {
        "S&P 500": "^GSPC",
        "MSCI World": "URTH", # ETF US
        "NASDAQ 100": "^NDX",
        "Euro Stoxx 50": "^STOXX50E",
        "MSCI Emerging Markets": "EEM", # ETF US
        "Russell 2000": "^RUT",
        "S&P 500 Equal Weight": "RSP" # ETF US
    },
    "TITANES GLOBALES (15)": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Alphabet": "GOOGL",
        "Amazon": "AMZN", "NVIDIA": "NVDA", "Meta Platforms": "META",
        "Tesla": "TSLA", "Berkshire Hathaway": "BRK-B", "Eli Lilly": "LLY",
        "JPMorgan Chase": "JPM", "Visa": "V", "Broadcom": "AVGO",
        "Novo Nordisk": "NVO", # US ADR para fundamentales completos
        "LVMH": "LVMUY", # US OTC para fundamentales
        "ASML": "ASML" # US ADR
    },
    "CURRENCIES": {
        "USD / EUR": "USDEUR=X",
        "USD / GBP": "USDGBP=X",
        "USD / JPY": "USDJPY=X"
    },
    "VOLATILITY & RISK": {
        "VIX (S&P 500 Volatility)": "^VIX",
        "V2TX (Euro Stoxx Volatility)": "^V2TX"
    },
    "BONDS (US ETFs)": {
        "US Treasury 20Y+": "TLT",
        "US Treasury 0-1Y": "SHV",
        "Intl Gov Bonds": "BNDX"
    },
    "COMMODITIES": {
        "Oil (Brent)": "BZ=F", "Gold": "GC=F", "Silver": "SI=F",
        "Copper": "HG=F", "Bitcoin": "BTC-USD"
    },
    "GLOBAL FACTORS (US ETFs)": {
        "Value": "VLUE", "Quality": "QUAL", "Dividend": "VYMI"
    },
    "EUROPE": {
        "UK (FTSE 100)": "^FTSE", "France (CAC 40)": "^FCHI",
        "Germany (DAX)": "^GDAXI", "Netherlands (AEX)": "^AEX",
        "Spain (IBEX 35)": "^IBEX", "Italy (FTSE MIB)": "FTSEMIB.MI"
    },
    "ASIA & LATAM (US ETFs)": {
        "Japan": "EWJ", "South Korea": "EWY", "India": "INDA",
        "China": "MCHI", "Brazil": "EWZ", "Mexico": "EWW",
        "Argentina (Merval USD CCL)": "MERVAL_USD" 
    },
    "US SECTORS (US ETFs)": {
        "Technology": "XLK", "Healthcare": "XLV", "Financials": "XLF",
        "Cons Discretionary": "XLY", "Communication": "XLC", "Industrials": "XLI",
        "Cons Staples": "XLP", "Energy": "XLE", "Utilities": "XLU", "Real Estate": "XLRE"
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
        
        # Extracción de precios y volumen
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

@st.cache_data(ttl=3600) # Fundamentales cacheados por 1 hora
def obtener_fundamentales(ticker):
    # Solo buscamos fundamentales si no es un índice puro o divisa
    if ticker.startswith("^") or "=" in ticker or ticker == "MERVAL_USD" or "-" in ticker and ticker != "BTC-USD":
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
                # Tomamos el vencimiento más cercano
                opt = tk.option_chain(expirations[0])
                puts_oi = opt.puts['openInterest'].sum()
                calls_oi = opt.calls['openInterest'].sum()
                vol_puts = opt.puts['volume'].sum()
                vol_calls = opt.calls['volume'].sum()
                
                ratio_oi = puts_oi / calls_oi if calls_oi > 0 else 0
                
                resultados.append({
                    "Titan": ticker,
                    "Vencimiento": expirations[0],
                    "Put/Call Ratio (OI)": round(ratio_oi, 2),
                    "Total Puts (Vol)": vol_puts,
                    "Total Calls (Vol)": vol_calls
                })
        except:
            continue
    return pd.DataFrame(resultados)

# --- BLOQUE 3: CÁLCULO DE MÉTRICAS ---
def calcular_metricas(df_precios, df_volumen, ticker, nombre, fecha_ref, es_hoy):
    if ticker not in df_precios.columns: raise ValueError("Sin datos")

    fecha_pandas = pd.to_datetime(fecha_ref).normalize()
    serie_precios = df_precios[ticker].loc[:fecha_pandas].dropna()
    
    if serie_precios.empty: raise ValueError("Sin datos")
    precio_actual = serie_precios.iloc[-1]
    
    def format_pct(val):
        return f"{round(val, 2)}%" if isinstance(val, (int, float)) else "-"
    
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
        high_52w = round(ultimo_anio.max(), 2)
        low_52w = round(ultimo_anio.min(), 2)
    except:
        high_52w, low_52w = "-", "-"

    # Volumen Relativo (Solo si es hoy)
    vol_pct_str = "-"
    if es_hoy and not df_volumen.empty and ticker in df_volumen.columns:
        serie_vol = df_volumen[ticker].loc[:fecha_pandas].dropna()
        if len(serie_vol) >= 63: # ~3 meses
            vol_hoy = serie_vol.iloc[-1]
            vol_promedio_3m = serie_vol.iloc[-63:].mean()
            if vol_promedio_3m > 0:
                vol_pct = ((vol_hoy / vol_promedio_3m) - 1) * 100
                vol_pct_str = format_pct(vol_pct)

    # Fundamentales (Solo si es hoy)
    fund = obtener_fundamentales(ticker) if es_hoy else {}

    return {
        "Nombre": nombre,
        "Precio": round(precio_actual, 2),
        "Low 52W": low_52w,
        "High 52W": high_52w,
        "1D": format_pct(pct_change(1)),
        "1W": format_pct(pct_change(5)),
        "1M": format_pct(pct_change(21)),
        "YTD": format_pct(ytd),
        "1Y": format_pct(pct_change(252)),
        "3Y": format_pct(pct_change(756)),
        "P/E": round(fund.get("PE", "-"), 2) if isinstance(fund.get("PE"), (int, float)) else fund.get("PE", "-"),
        "Beta": round(fund.get("Beta", "-"), 2) if isinstance(fund.get("Beta"), (int, float)) else fund.get("Beta", "-"),
        "Target P.": round(fund.get("Target", "-"), 2) if isinstance(fund.get("Target"), (int, float)) else fund.get("Target", "-"),
        "% Vol vs 3M": vol_pct_str,
        "BPA (TTM)": round(fund.get("EPS", "-"), 2) if isinstance(fund.get("EPS"), (int, float)) else fund.get("EPS", "-"),
        "Rec.": fund.get("Rec", "-")
    }

# --- BLOQUE 4: INTERFAZ MASTER COMMAND ---
col_title, col_cal = st.columns([2, 1])
with col_title:
    st.title("🛡️ Master Command by PS")
with col_cal:
    st.write("") # Espaciador
    fecha_seleccionada = st.date_input(
        "🗓️ Fecha de Cálculo", 
        value=date.today(), 
        max_value=date.today()
    )

es_hoy = fecha_seleccionada == date.today()

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
            return f'background-color: {color}; color: white'
        except: return ''
    return ''

with st.spinner('Consolidando datos de mercado, opciones y fundamentales...'):
    df_precios, df_volumen = obtener_precios()
    
    if df_precios.empty:
        st.error("🚨 Error de conexión con el proveedor de datos.")
    else:
        for categoria, items in ACTIVOS.items():
            st.subheader(categoria)
            lista_resultados = []
            
            for nombre, ticker in items.items():
                try:
                    metrica = calcular_metricas(df_precios, df_volumen, ticker, nombre, fecha_seleccionada, es_hoy)
                    lista_resultados.append(metrica)
                except: continue
            
            if lista_resultados:
                df_display = pd.DataFrame(lista_resultados)
                st.dataframe(
                    df_display.style.applymap(color_heatmap, subset=['1D', '1W', '1M', 'YTD', '1Y', '3Y']),
                    hide_index=True,
                    use_container_width=True
                )

        # MÓDULO DE POSICIÓN ABIERTA (Solo se muestra si la fecha es hoy)
        if es_hoy:
            st.markdown("---")
            st.subheader("🔥 Sentimiento Institucional Opciones (Titanes Globales)")
            st.caption("Ratio mayor a 1.0 = Sentimiento Bajista/Cobertura. Menor a 1.0 = Sentimiento Alcista.")
            tickers_titanes = list(ACTIVOS["TITANES GLOBALES (15)"].values())
            df_opciones = obtener_opciones_titanes(tickers_titanes)
            if not df_opciones.empty:
                st.dataframe(df_opciones, hide_index=True, use_container_width=True)
            else:
                st.info("Datos de cadena de opciones no disponibles en este momento.")

# --- BLOQUE 5: TABLA DE EQUIVALENCIAS UCITS ---
st.markdown("---")
st.subheader("🇪🇺 Tabla de Equivalencias: US ETFs a UCITS (Europa)")
ucits_data = {
    "Activo / Exposición": ["MSCI World", "Emerging Markets", "S&P 500 Equal Weight", "US Treasury 20Y+", "US Treasury 0-1Y", "US Technology", "US Healthcare"],
    "US Ticker (Usado)": ["URTH", "EEM", "RSP", "TLT", "SHV", "XLK", "XLV"],
    "UCITS Equivalente (EUR)": ["IWDA.L / EUNL.DE", "EMIM.L", "SPXW.L / XDEW.DE", "DTLA.L", "VDST.L", "IUIT.L", "IUHC.L"]
}
st.table(pd.DataFrame(ucits_data))