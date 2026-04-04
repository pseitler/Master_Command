import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Market Tracker Pro")

# --- BLOQUE 1: DICCIONARIO MAESTRO DE ACTIVOS ---
ACTIVOS = {
    "MAJOR INDICES (UCITS)": {
        "S&P 500": "VUSA.L",
        "MSCI World": "IWDA.L",
        "NASDAQ 100": "EQQQ.L",
        "Euro Stoxx 50": "SX5E.EX",
        "MSCI Emerging Markets": "EMIM.L",
        "Russell 2000": "IUSN.DE",
        "S&P 500 Equal Weight": "SPXW.L"
    },
    "TITANES GLOBALES (15)": {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Alphabet": "GOOGL",
        "Amazon": "AMZN",
        "NVIDIA": "NVDA",
        "Meta Platforms": "META",
        "Tesla": "TSLA",
        "Berkshire Hathaway": "BRK-B",
        "Eli Lilly": "LLY",
        "JPMorgan Chase": "JPM",
        "Visa": "V",
        "Broadcom": "AVGO",
        "Novo Nordisk": "NOVO-B.CO",
        "LVMH": "MC.PA",
        "ASML": "ASML.AS"
    },
    "CURRENCIES": {
        "EUR / USD": "EURUSD=X",
        "EUR / GBP": "EURGBP=X",
        "EUR / JPY": "EURJPY=X"
    },
    "VOLATILITY & RISK": {
        "VIX (S&P 500 Volatility)": "^VIX",
        "V2TX (Euro Stoxx Volatility)": "^V2TX"
    },
    "BONDS (UCITS)": {
        "US Treasury 20Y+": "DTLA.L",
        "US Treasury 0-1Y": "VDST.L",
        "Euro Gov Bonds": "EUNA.DE",
        "Euro Corporate IG": "IEAC.L"
    },
    "COMMODITIES": {
        "Oil (Brent)": "BZ=F",
        "Gold (ETC)": "IGLN.L",
        "Silver (ETC)": "ISLN.L",
        "Copper": "HG=F",
        "Bitcoin": "BTC-USD"
    },
    "GLOBAL FACTORS (UCITS)": {
        "MSCI World Value": "IWVL.L",
        "MSCI World Quality": "IWQU.L",
        "Global Dividend": "VHYL.L"
    },
    "EUROPE": {
        "UK (FTSE 100)": "^FTSE",
        "France (CAC 40)": "^FCHI",
        "Germany (DAX)": "^GDAXI",
        "Netherlands (AEX)": "^AEX",
        "Spain (IBEX 35)": "^IBEX",
        "Italy (FTSE MIB)": "FTSEMIB.MI"
    },
    "ASIA (UCITS)": {
        "Japan": "IJPN.L",
        "South Korea": "CSKR.L",
        "India": "NDIA.L",
        "China": "HMCH.L",
        "Hong Kong": "^HSI"
    },
    "LATAM": {
        "Brazil": "EWZ",
        "Mexico": "EWW",
        "MSCI EM LatAm": "LTAM.L",
        "Argentina (Merval USD CCL)": "MERVAL_USD" 
    },
    "US SECTORS (UCITS)": {
        "Technology": "IUIT.L",
        "Healthcare": "IUHC.L",
        "Financials": "IUFS.L",
        "Cons Discretionary": "IUCD.L",
        "Communication": "CMTC.L",
        "Industrials": "IUDS.L",
        "Cons Staples": "IUCG.L",
        "Energy": "IUES.L",
        "Utilities": "IUUS.L",
        "Real Estate": "IUSP.L"
    },
    "EU SECTORS (UCITS)": {
        "EU Banks": "EXV1.DE",
        "EU Healthcare": "EXV4.DE",
        "EU Industrials": "EXV6.DE",
        "EU Energy": "EXV5.DE",
        "EU Technology": "EXV3.DE",
        "EU Cons Staples": "EXV9.DE",
        "EU Telecoms": "EXV2.DE",
        "EU Utilities": "EXV7.DE",
        "EU Materials": "EXV8.DE",
        "EU Real Estate": "EXI5.DE"
    }
}

TICKERS_AUXILIARES = ["^MERV", "GGAL.BA", "GGAL"]

# --- BLOQUE 2: MOTOR DE DATOS Y LÓGICA MERVAL ---
@st.cache_data(ttl=300) 
def obtener_datos():
    all_tickers = []
    for categoria in ACTIVOS.values():
        all_tickers.extend(list(categoria.values()))
    
    if "MERVAL_USD" in all_tickers:
        all_tickers.remove("MERVAL_USD")
        
    all_tickers.extend(TICKERS_AUXILIARES)
    all_tickers = list(set(all_tickers)) 
    
    # IMPORTANTE: Aumentamos a 10 años para poder viajar al pasado y seguir teniendo 3 años previos
    df = yf.download(all_tickers, period="10y", interval="1d")['Adj Close']

# NUEVA LÍNEA: Limpiamos la zona horaria para que coincida con el calendario
    df.index = df.index.tz_localize(None)
    
    try:
        merv = df['^MERV'].ffill()
        ggal_ba = df['GGAL.BA'].ffill() 
        ggal_us = df['GGAL'].ffill()    
        
        ccl = ggal_ba / (ggal_us * 10)
        merval_usd = merv / ccl
        
        df['MERVAL_USD'] = merval_usd
    except Exception as e:
        df['MERVAL_USD'] = pd.Series(dtype=float) 
        
    return df

# --- BLOQUE 3: CÁLCULO DE MÉTRICAS FINANCIERAS EN EL TIEMPO ---
# Se añade el parámetro fecha_ref para saber hasta dónde mirar
def calcular_metricas(df, ticker, nombre, fecha_ref):
    # Convertimos la fecha del calendario a un formato que entienda la base de datos
    fecha_pandas = pd.to_datetime(fecha_ref)
    
    # CORTAMOS LA HISTORIA: Eliminamos todos los datos que ocurrieron después de la fecha elegida
    serie = df[ticker].loc[:fecha_pandas].dropna()
    
    if serie.empty:
        raise ValueError("Sin datos para esta fecha")
        
    # El "precio actual" ahora es el precio del último día válido hasta la fecha elegida
    precio_actual = serie.iloc[-1]
    fecha_precio_real = serie.index[-1].strftime('%d-%m-%Y') # Guardamos qué día exacto tomó (por si fue fin de semana)
    
    def pct_change(days):
        try:
            inicio = serie.iloc[-days]
            return ((precio_actual - inicio) / inicio) * 100
        except: return 0.0

    # Cálculo YTD ajustado: Busca el inicio del año de la fecha elegida
    try:
        inicio_anio = serie.loc[serie.index.year == fecha_pandas.year].iloc[0]
        ytd = ((precio_actual - inicio_anio) / inicio_anio) * 100
    except:
        ytd = 0.0
    
    # Cálculo de 52 Semanas ajustado a la fecha elegida
    try:
        ultimo_anio = serie.iloc[-252:]
        high_52w = ((precio_actual - ultimo_anio.max()) / ultimo_anio.max()) * 100
        low_52w = ((precio_actual - ultimo_anio.min()) / ultimo_anio.min()) * 100
    except:
        high_52w, low_52w = 0.0, 0.0

    return {
        "Nombre": nombre,
        "Ticker": ticker,
        "Precio": round(precio_actual, 2),
        "Fecha Ref.": fecha_precio_real, # Nueva columna útil
        "Low 52W": f"{round(low_52w, 1)}%",
        "High 52W": f"{round(high_52w, 1)}%",
        "1D": round(serie.pct_change().iloc[-1] * 100, 2),
        "1W": round(pct_change(5), 2),
        "1M": round(pct_change(21), 2),
        "YTD": round(ytd, 2),
        "1Y": round(pct_change(252), 2),
        "3Y": round(pct_change(756), 2)
    }

# --- BLOQUE 4: MOTOR VISUAL Y RENDERING ---
st.title("📊 Global Market & Macro Tracker")

# MÁQUINA DEL TIEMPO: Interfaz de Calendario
col1, col2 = st.columns([1, 3])
with col1:
    fecha_seleccionada = st.date_input(
        "🗓️ Seleccionar Fecha de Análisis", 
        value=date.today(), # Por defecto arranca hoy
        max_value=date.today() # No permite elegir fechas del futuro
    )

st.caption(f"Calculando rentabilidades respecto a los precios de cierre del: {fecha_seleccionada.strftime('%d-%m-%Y')}")

def color_heatmap(val):
    try:
        val = float(val)
        if val > 3: color = '#1E7B1E' 
        elif val > 1: color = '#228B22' 
        elif val > 0: color = '#90EE90' 
        elif val < -3: color = '#8B0000' 
        elif val < -1: color = '#FF4500' 
        elif val < 0: color = '#FFB6C1' 
        else: color = 'transparent'
        return f'background-color: {color}; color: {"white" if abs(val) > 1 else "black"}'
    except:
        return ''

with st.spinner(f'Procesando mercado y calculando métricas históricas al {fecha_seleccionada.strftime("%d-%m-%Y")}...'):
    precios = obtener_datos()
    
    for categoria, items in ACTIVOS.items():
        st.subheader(categoria)
        lista_resultados = []
        
        for nombre, ticker in items.items():
            try:
                # Enviamos la fecha del calendario a la función matemática
                metrica = calcular_metricas(precios, ticker, nombre, fecha_seleccionada)
                lista_resultados.append(metrica)
            except Exception as e:
                continue
        
        if lista_resultados:
            df_display = pd.DataFrame(lista_resultados)
            st.dataframe(
                df_display.style.map(color_heatmap, subset=['1D', '1W', '1M', 'YTD', '1Y', '3Y']),
                hide_index=True,
                use_container_width=True
            )
