# 🛡️ Master Command by PS

**Master Command** es un terminal financiero y cuantitativo de código abierto construido con Python y Streamlit. Diseñado con una arquitectura de grado institucional, permite monitorizar los mercados globales, evaluar riesgos estructurales de cartera, analizar liquidez macroeconómica y medir el sentimiento del mercado de opciones en tiempo real.

## 🚀 Características Principales

* **Radar Macroeconómico (FED):** Conexión directa con la base de datos de la Reserva Federal (FRED) para monitorizar inyecciones de liquidez (Balance de la FED), Tasas de Interés, Inflación (CPI) y Desempleo.
* **Análisis Cuantitativo Integrado:** Cálculo en tiempo real de métricas de riesgo y momentum:
  * RSI (Índice de Fuerza Relativa a 14 días).
  * Distancia porcentual a la Media Móvil de 200 días (SMA 200).
  * Máximo Drawdown (MDD) a 1 año.
* **Matriz de Correlación:** Mapa de calor algorítmico que cruza el rendimiento anual de los "Titanes Globales" para evaluar la verdadera diversificación de la cartera.
* **Sentimiento Institucional (Opciones):** Extracción automatizada de la Cadena de Opciones para calcular el ratio Put/Call y la Posición Abierta (Open Interest).
* **Fundamentales Forward y Precios:** Datos actualizados de P/E, BPA (EPS), Beta, Precios Objetivo y Volumen Relativo vs. media de 3 meses.
* **"Máquina del Tiempo" (Análisis Histórico):** Motor de recálculo que permite seleccionar fechas pasadas y reajustar todas las rentabilidades porcentuales (1D, 1W, 1M, YTD, 1Y, 3Y) relativas a ese día específico.
* **UX/UI Profesional:** Diseño de terminal oscuro (Dark Mode), mapa de calor visual para rendimientos, encabezados y columnas congeladas (Sticky Columns) y enlaces automáticos a los gráficos de *TradingView*.
* **Soporte Europeo (UCITS):** Diccionario integrado de equivalencias entre ETFs del mercado estadounidense e instrumentos UCITS europeos.

## 📡 Arquitectura de Datos (APIs)

El tablero se alimenta de forma automatizada mediante librerías de extracción de datos públicos:
1. **Yahoo Finance (`yfinance`):** Utilizado para descargar hasta 10 años de historia de precios, datos fundamentales de empresas y cadenas de opciones.
2. **FRED (`pandas-datareader`):** Utilizado para la extracción de métricas macroeconómicas directamente de los servidores de la Reserva Federal de San Luis.

## 🛠️ Instalación y Despliegue Local

Para ejecutar Master Command en tu propia máquina, sigue estos pasos:

1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/nombre-del-repo.git](https://github.com/tu-usuario/nombre-del-repo.git)
   cd nombre-del-repo