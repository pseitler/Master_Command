import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Market Tracker Pro")

# --- BLOQUE 1: DICCIONARIO MAESTRO DE ACTIVOS ---
# Contiene la estructura completa. Se priorizan ETFs UCITS (.L, .DE, .AS, .PA) y acciones directas.
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
        "Argentina (Merval USD CCL)": "MERVAL_USD" # Ticker sintético creado por nosotros
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

# Tickers auxiliares necesarios para calcular el Merval en USD CCL
TICKERS_AUXILIARES = ["^MERV", "GGAL.BA", "GGAL"]

# --- BLOQUE 2: MOTOR DE DATOS Y LÓGICA MERVAL ---
@st.cache_data(ttl=300) # Guarda los datos 5 minutos para no saturar Yahoo Finance
def obtener_datos():
    # Recopilamos todos los tickers, incluyendo los auxiliares
    all_tickers = []
    for categoria in ACTIVOS.values():
        all_tickers.extend(list(categoria.values()))
    
    # Eliminamos el ticker sintético antes de descargar, ya que Yahoo no lo conoce
    if "MERVAL_USD" in all_tickers:
        all_tickers.remove("MERVAL_USD")
        
    all_tickers.extend(TICKERS_AUXILIARES)
    all_tickers = list(set(all_tickers)) # Eliminamos duplicados
    
    # Descargamos 4 años de historia para los cálculos de largo plazo
    df = yfinance.download(all_tickers, period="4y", interval="1d")['Adj Close']
    
    # Lógica de cálculo: Merval Contado Con Liquidación (CCL)
    try:
        # Llenamos vacíos (días festivos) repitiendo el último precio válido (ffill)
        merv = df['^MERV'].ffill()
        ggal_ba = df['GGAL.BA'].ffill() # Galicia en Pesos
        ggal_us = df['GGAL'].ffill()    # Galicia ADR en USD
        
        # El ratio de conversión del ADR de Galicia es 10 a 1
        ccl = ggal_ba / (ggal_us * 10)
        merval_usd = merv / ccl
        
        # Añadimos nuestra serie sintética al dataframe principal
        df['MERVAL_USD'] = merval_usd
    except Exception as e:
        df['MERVAL_USD'] = pd.Series(dtype=float) # Columna vacía si falla la conexión
        
    return df

# --- BLOQUE 3: CÁLCULO DE MÉTRICAS FINANCIERAS ---
def calcular_metricas(df, ticker, nombre):
    # Extraemos la serie de precios del activo, eliminando días sin cotización
    serie = df[ticker].dropna()
    if serie.empty:
        raise ValueError("Sin datos")
        
    precio_actual = serie.iloc[-1]
    
    def pct_change(days):
        try:
            # Buscamos el precio de hace 'X' días hábiles
            inicio = serie.iloc[-days]
            return ((precio_actual - inicio) / inicio) * 100
        except: return 0.0

    # Cálculo Year-to-Date (YTD): Rendimiento desde el 1 de enero
    try:
        inicio_anio = serie.loc[serie.index.year == datetime.now().year].iloc[0]
        ytd = ((precio_actual - inicio_anio) / inicio_anio) * 100
    except:
        ytd = 0.0
    
    # Cálculo de los rangos de 52 Semanas (1 año bursátil = 252 días)
    try:
        ultimo_anio = serie.iloc[-252:]
        high_52w = ((precio_actual - ultimo_anio.max()) / ultimo_anio.max()) * 100
        low_52w = ((precio_actual - ultimo_anio.min()) / ultimo_anio.min()) * 100
    except:
        high_52w, low_52w = 0.0, 0.0

    # Construimos la fila de resultados para la tabla
    return {
        "Nombre": nombre,
        "Ticker": ticker,
        "Precio": round(precio_actual, 2),
        "Low 52W": f"{round(low_52w, 1)}%",
        "High 52W": f"{round(high_52w, 1)}%",
        "1D": round(serie.pct_change().iloc[-1] * 100, 2),
        "1W": round(pct_change(5), 2),
        "1M": round(pct_change(21), 2),
        "YTD": round(ytd, 2),
        "1Y": round(pct_change(252), 2),
        "3Y": round(pct_change(756), 2)
    }

# --- BLOQUE 4: MOTOR VISUAL Y RENDERIZADO (FRONTEND) ---
st.title("📊 Global Market & Macro Tracker")
st.caption(f"Última actualización: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} (Hora Servidor)")

# Función de formato condicional (Heatmap)
def color_heatmap(val):
    try:
        val = float(val)
        # Escala de colores inspirada en terminales de Wall Street
        if val > 3: color = '#1E7B1E' # Verde muy oscuro
        elif val > 1: color = '#228B22' # Verde fuerte
        elif val > 0: color = '#90EE90' # Verde claro
        elif val < -3: color = '#8B0000' # Rojo muy oscuro
        elif val < -1: color = '#FF4500' # Rojo fuerte
        elif val < 0: color = '#FFB6C1' # Rojo claro
        else: color = 'transparent'
        return f'background-color: {color}; color: {"white" if abs(val) > 1 else "black"}'
    except:
        return ''

with st.spinner('Procesando datos del mercado global y calculando CCL...'):
    precios = obtener_datos()
    
    # Recorremos cada categoría de nuestro diccionario y creamos una tabla
    for categoria, items in ACTIVOS.items():
        st.subheader(categoria)
        lista_resultados = []
        
        for nombre, ticker in items.items():
            try:
                metrica = calcular_metricas(precios, ticker, nombre)
                lista_resultados.append(metrica)
            except Exception as e:
                # Si un ticker falla (ej. día festivo local), lo saltamos para no romper el tablero
                continue
        
        if lista_resultados:
            df_display = pd.DataFrame(lista_resultados)
            # Ocultamos el índice numérico por defecto de Pandas para mayor limpieza visual
            st.dataframe(
                df_display.style.map(color_heatmap, subset=['1D', '1W', '1M', 'YTD', '1Y', '3Y']),
                hide_index=True,
                use_container_width=True
            )
