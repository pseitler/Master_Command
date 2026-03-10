# 📊 Market Tracker Pro

Un tablero de control financiero (Dashboard) interactivo y en tiempo real, diseñado para monitorear el estado macroeconómico y los mercados globales. 

Esta herramienta está optimizada para el acceso desde Europa, utilizando ETFs en formato UCITS, y cuenta con una función especial para calcular el valor real del mercado argentino mediante el tipo de cambio Contado Con Liquidación (CCL).



---

## 🚀 Características Principales

* **Seguimiento UCITS:** Los índices globales, sectores y bonos están configurados utilizando tickers de ETFs europeos (cotizados en Londres, Xetra, etc.), reflejando el acceso real y los horarios de mercado europeos.
* **Titanes Globales:** Monitoreo en tiempo real de las 15 empresas más influyentes del mundo, combinando las grandes tecnológicas de EE. UU. (Las 7 Magníficas) con líderes europeos (LVMH, ASML, Novo Nordisk) y gigantes de sectores defensivos y financieros.
* **Cálculo de Merval en USD (CCL):** El sistema extrae el índice Merval en pesos y lo divide automáticamente por el tipo de cambio implícito (calculado en tiempo real usando la cotización local y el ADR de Grupo Galicia en Nueva York) para mostrar el rendimiento real en moneda dura.
* **Mapa de Calor Visual (Heatmap):** Formato condicional de colores que imita los terminales profesionales, permitiendo identificar rápidamente tendencias diarias, semanales, mensuales y anuales.
* **Indicadores Macro:** Integración de divisas clave (EUR/USD), materias primas estratégicas (Cobre, Petróleo, Oro) y medidores de volatilidad (VIX y V2TX).

---

## 📂 Estructura de Archivos

El proyecto se compone estrictamente de los siguientes archivos:

1. **`app.py`**: Es el motor principal de la aplicación. Contiene toda la lógica programada en Python utilizando la librería Streamlit para la interfaz visual y `yfinance` para la extracción de datos en tiempo real.
2. **`requirements.txt`**: El listado de dependencias. Le indica al servidor qué librerías matemáticas y visuales debe instalar para que el código de `app.py` funcione correctamente.
3. **`README.md`**: Este archivo de documentación.

---

## ⚙️ Instrucciones de Despliegue en Render

Este proyecto está diseñado para ser alojado en la plataforma Render. Sigue estos pasos para ponerlo en producción:

### Paso 1: Preparar el Repositorio
1. Crea una cuenta en [GitHub](https://github.com/) si no tienes una.
2. Crea un nuevo repositorio (puede ser privado).
3. Sube los archivos `app.py`, `requirements.txt` y este `README.md` a la rama principal (`main` o `master`).

### Paso 2: Configurar Render
1. Inicia sesión en [Render](https://render.com/).
2. Haz clic en el botón **"New"** y selecciona **"Web Service"**.
3. Conecta tu cuenta de GitHub y selecciona el repositorio que acabas de crear.
4. Completa la configuración con los siguientes parámetros exactos:
   * **Name:** `market-tracker-pro` (o el nombre que prefieras).
   * **Region:** Selecciona la región más cercana a ti (ej. Frankfurt).
   * **Branch:** `main` (o la rama donde subiste los archivos).
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Selecciona tu plan (Free o Básico) y haz clic en **"Create Web Service"**.

### Paso 3: Monitoreo
Render comenzará a compilar la aplicación. Este proceso puede tardar un par de minutos la primera vez. Una vez finalizado, verás un enlace verde (ej. `https://market-tracker-pro.onrender.com`). Haz clic en él para ver tu tablero operativo en cualquier dispositivo.

---

## 🛠️ Tecnologías Utilizadas

* **Python 3:** Lenguaje de programación principal.
* **Streamlit:** Framework para la creación de la interfaz web interactiva.
* **YFinance:** API para la descarga de datos históricos y en tiempo real de Yahoo Finance.
* **Pandas:** Librería para la manipulación, limpieza y estructuración de los datos financieros.
