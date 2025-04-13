# 📊 Dashboard de Análisis de Ventas

Este proyecto es una aplicación interactiva desarrollada con [Streamlit](https://streamlit.io/) que permite visualizar y analizar datos de ventas de forma dinámica y atractiva. Está diseñado para ayudar a equipos comerciales, analistas y tomadores de decisiones a identificar tendencias, evaluar el rendimiento y segmentar clientes.

## 🚀 Características principales

- **KPIs generales**: valor total, cantidad, ticket promedio, clientes y productos únicos.
- **Tasa de crecimiento mensual**: evolución y comparación porcentual entre meses.
- **Análisis temporal**: tendencias a lo largo del tiempo y mapa de calor por mes/año.
- **Índice de estacionalidad**: identifica meses fuertes o débiles en ventas.
- **Comparación de períodos**: comparación entre dos meses/años específicos.
- **Segmentación de clientes**: análisis tipo RFM simplificado por valor y frecuencia.
- **Análisis por cliente**: clientes top y frecuencia de compra.
- **Análisis por producto y categoría**: productos más vendidos, drill-down por categoría/subcategoría.
- **Tasa de penetración**: popularidad de categorías por % de clientes.

## 📂 Estructura de archivos

- `reporte.py`: script principal de la app Streamlit.
- `Hechos_Ventas_Agrupado.csv`: dataset principal de ventas (referencia en el script).
- `Dim_Cliente.csv`: información detallada de los clientes.

## 📦 Requisitos

Asegúrate de tener Python 3.8+ y luego instala las dependencias necesarias:

```bash
pip install streamlit pandas plotly numpy
