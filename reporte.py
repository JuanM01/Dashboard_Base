import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import base64
from io import BytesIO
from datetime import datetime
import calendar

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Ventas",
    page_icon="📊",
    layout="wide"
)

# Mapeo de números de mes a nombres
MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# Función para agrupar valores pequeños en "Otros"
def agrupar_pequenos(df, columna_categoria, columna_valor, umbral_porcentaje=4):
    # Calcular el total
    total = df[columna_valor].sum()
    
    # Calcular el porcentaje que representa cada categoría
    df_con_porcentaje = df.copy()
    df_con_porcentaje['porcentaje'] = df_con_porcentaje[columna_valor] / total * 100
    
    # Separar categorías grandes y pequeñas
    grandes = df_con_porcentaje[df_con_porcentaje['porcentaje'] >= umbral_porcentaje]
    pequenos = df_con_porcentaje[df_con_porcentaje['porcentaje'] < umbral_porcentaje]
    
    # Si hay categorías pequeñas, agruparlas
    if not pequenos.empty:
        otros = pd.DataFrame({
            columna_categoria: ['Otros'],
            columna_valor: [pequenos[columna_valor].sum()],
            'porcentaje': [pequenos['porcentaje'].sum()]
        })
        # Combinar grandes y otros
        resultado = pd.concat([grandes, otros], ignore_index=True)
    else:
        resultado = grandes
    
    return resultado.sort_values(columna_valor, ascending=False)

# Sidebar para filtros
st.sidebar.title("Filtros")

# Cargar datos
@st.cache_data
def load_data():
    # Cargar ventas
    df = pd.read_csv(r"C:\Users\ACER\OneDrive\Documentos\rompecabezas\dimensiones\Hechos_Ventas_Agrupado.csv")
    df['fecha'] = pd.to_datetime(df['anio'].astype(str) + '-' + df['mes'].astype(str) + '-01')
    df['cod_clte'] = df['cod_clte'].astype(str)

    # Cargar clientes
    df_clientes = pd.read_csv(r"C:\Users\ACER\OneDrive\Documentos\rompecabezas\dimensiones\Dim_Cliente.csv", dtype={'cod_clte': str})

    return df, df_clientes

try:
    df, df_clientes = load_data()
    data_load_state = st.sidebar.success('Datos cargados correctamente!')
except Exception as e:
    st.sidebar.error(f'Error al cargar los datos: {e}')
    st.stop()

# Filtros interactivos en sidebar
años_disponibles = sorted(df['anio'].unique())
categorias_disponibles = sorted(df['categoria'].unique())

# Filtro de año
años_seleccionados = st.sidebar.multiselect(
    "Seleccionar Años",
    años_disponibles,
    default=años_disponibles[-1:]  # Por defecto, el último año
)

# Filtro de categoría
categorias_seleccionadas = st.sidebar.multiselect(
    "Seleccionar Categorías",
    categorias_disponibles,
    default=[]  # Por defecto, todas las categorías
)

# Aplicar filtros
if años_seleccionados:
    df_filtrado = df[df['anio'].isin(años_seleccionados)]
else:
    df_filtrado = df

if categorias_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['categoria'].isin(categorias_seleccionadas)]

# Filtro para comparación de períodos
st.sidebar.subheader("Comparación de Períodos")
comparar_periodos = st.sidebar.checkbox("Activar comparación de períodos")

if comparar_periodos:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        periodo1_año = st.selectbox("Año 1", años_disponibles, index=len(años_disponibles)-2 if len(años_disponibles) > 1 else 0)
        periodo1_mes = st.selectbox("Mes 1", range(1, 13), index=0, format_func=lambda x: MESES[x])
    with col2:
        periodo2_año = st.selectbox("Año 2", años_disponibles, index=len(años_disponibles)-1)
        periodo2_mes = st.selectbox("Mes 2", range(1, 13), index=0, format_func=lambda x: MESES[x])

# Título
st.title('Dashboard de Análisis de Ventas')
st.markdown("""
Este dashboard proporciona un análisis completo de las ventas, permitiendo visualizar tendencias, 
identificar patrones y segmentar clientes para tomar decisiones estratégicas basadas en datos.
""")

# KPIs
st.header('KPIs Generales')
st.markdown("""
Los siguientes indicadores muestran el rendimiento general de las ventas en el período seleccionado.
""")

col1, col2, col3, col4, col5 = st.columns(5)

valor_total = df_filtrado['valor_total'].sum()
cantidad_total = df_filtrado['cantidad_total'].sum()
ticket_promedio = valor_total / len(df_filtrado) if len(df_filtrado) > 0 else 0
clientes_unicos = df_filtrado['cod_clte'].nunique()
productos_unicos = df_filtrado['art_codi'].nunique()

def formatear_valor(valor):
    if valor >= 1e12:
        return f"${valor / 1e12:.2f} billones"
    elif valor >= 1e9:
        return f"${valor / 1e9:.2f} mil millones"
    elif valor >= 1e6:
        return f"${valor / 1e6:.2f} millones"
    elif valor >= 1e3:
        return f"${valor / 1e3:.2f} mil"
    else:
        return f"${valor:,.2f}"

with col1:
    st.metric("Valor Total", formatear_valor(valor_total))
with col2:
    st.metric("Cantidad Total", formatear_valor(cantidad_total))
with col3:
    st.metric("Ticket Promedio", formatear_valor(ticket_promedio))
with col4:
    st.metric("Clientes Únicos", f"{clientes_unicos:,}")
with col5:
    st.metric("Productos Únicos", f"{productos_unicos:,}")

# Tasa de Crecimiento (Mes a Mes con Filtro de Año)
st.header('Tasa de Crecimiento')
st.markdown("""
Este gráfico muestra la evolución de las ventas mes a mes y el porcentaje de crecimiento respecto al mes anterior.
Las barras verdes indican crecimiento positivo, mientras que las rojas señalan decrecimiento.
""")

# Selector de año para tasa de crecimiento
año_crecimiento = st.selectbox(
    "Seleccionar Año para Análisis de Crecimiento",
    años_disponibles,
    index=len(años_disponibles)-1
)

# Calcular tasa de crecimiento mensual
df_año = df[df['anio'] == año_crecimiento]
ventas_mensuales = df_año.groupby('mes')['valor_total'].sum().reset_index()
ventas_mensuales['crecimiento'] = ventas_mensuales['valor_total'].pct_change() * 100

# Añadir nombres de meses
ventas_mensuales['nombre_mes'] = ventas_mensuales['mes'].map(MESES)

# Crear gráfico combinado (línea para ventas, barras para crecimiento)
fig_crecimiento = go.Figure()

# Añadir línea de ventas
fig_crecimiento.add_trace(
    go.Scatter(
        x=ventas_mensuales['nombre_mes'], 
        y=ventas_mensuales['valor_total'],
        mode='lines+markers',
        name='Ventas Mensuales',
        line=dict(color='royalblue', width=3)
    )
)

# Añadir barras de crecimiento
fig_crecimiento.add_trace(
    go.Bar(
        x=ventas_mensuales['nombre_mes'],
        y=ventas_mensuales['crecimiento'],
        name='% Crecimiento',
        marker_color=ventas_mensuales['crecimiento'].apply(
            lambda x: 'green' if x > 0 else 'red'
        ),
        yaxis='y2'
    )
)

# Configurar ejes y layout
fig_crecimiento.update_layout(
    title=f'Crecimiento Mensual de Ventas en {año_crecimiento}',
    xaxis=dict(title='Mes', categoryorder='array', categoryarray=list(MESES.values())),
    yaxis=dict(title='Valor Total ($)', side='left'),
    yaxis2=dict(title='% Crecimiento', side='right', overlaying='y', showgrid=False),
    legend=dict(x=0.01, y=0.99),
    hovermode='x unified'
)

# Añadir línea de referencia en 0% para el crecimiento
fig_crecimiento.add_shape(
    type='line',
    x0=0,
    y0=0,
    x1=1,
    y1=0,
    yref='y2',
    xref='paper',
    line=dict(color='gray', width=1, dash='dash')
)

st.plotly_chart(fig_crecimiento, use_container_width=True)

# Análisis Temporal
st.header('Análisis Temporal')
st.markdown("""
Estos gráficos muestran la evolución de las ventas a lo largo del tiempo y la distribución por mes y año.
La tendencia permite identificar patrones estacionales y el mapa de calor facilita la comparación entre períodos.
""")

col1, col2 = st.columns(2)

with col1:
    # Tendencia de ventas
    ventas_tiempo = df_filtrado.groupby(['fecha']).agg({
        'valor_total': 'sum'
    }).reset_index()
    
    fig = px.line(
        ventas_tiempo, 
        x='fecha', 
        y='valor_total',
        title='Tendencia de Ventas por Mes',
        labels={'valor_total': 'Valor Total ($)', 'fecha': 'Fecha'}
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(
            tickformat='%b %Y',
            tickangle=-45
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Mapa de calor por mes y año
    heatmap_data = df_filtrado.groupby(['anio', 'mes']).agg({
        'valor_total': 'sum'
    }).reset_index()
    
    if not heatmap_data.empty:
        pivot_data = heatmap_data.pivot(index='anio', columns='mes', values='valor_total')
        
        # Obtener las columnas reales (meses) presentes en los datos
        meses_presentes = sorted(pivot_data.columns)
        
        # Crear etiquetas de meses con nombres
        etiquetas_meses = [MESES.get(m, f"Mes {m}") for m in meses_presentes]
        
        fig = px.imshow(
            pivot_data,
            labels=dict(x="Mes", y="Año", color="Valor Total"),
            x=etiquetas_meses,
            y=pivot_data.index,
            title="Mapa de Calor de Ventas por Mes y Año",
            color_continuous_scale="Viridis"
        )
        
        fig.update_layout(
            xaxis=dict(side='bottom')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay suficientes datos para generar el mapa de calor.")

# Índice de Estacionalidad
st.header('Índice de Estacionalidad')
st.markdown("""
Este gráfico muestra qué meses tienen ventas por encima o por debajo del promedio anual.
Un índice mayor a 1.0 indica que el mes tiene ventas superiores al promedio, mientras que 
valores menores a 1.0 indican ventas por debajo del promedio. Es útil para identificar 
patrones estacionales y planificar estrategias específicas para cada período.
""")

# Calcular índice de estacionalidad
ventas_por_mes = df.groupby('mes')['valor_total'].sum()
promedio_mensual = ventas_por_mes.mean()
indice_estacionalidad = (ventas_por_mes / promedio_mensual).reset_index()
indice_estacionalidad.columns = ['mes', 'indice']

# Añadir nombres de meses
indice_estacionalidad['nombre_mes'] = indice_estacionalidad['mes'].map(MESES)

# Crear gráfico de estacionalidad
fig_estacionalidad = px.bar(
    indice_estacionalidad,
    x='nombre_mes',
    y='indice',
    title='Índice de Estacionalidad por Mes',
    labels={'indice': 'Índice (1.0 = Promedio)', 'nombre_mes': 'Mes'},
    color='indice',
    color_continuous_scale=['red', 'yellow', 'green'],
    range_color=[0.5, 1.5]
)

# Ordenar meses cronológicamente
fig_estacionalidad.update_layout(
    xaxis=dict(
        categoryorder='array', 
        categoryarray=list(MESES.values())
    ),
    yaxis=dict(range=[0, max(indice_estacionalidad['indice']) * 1.1])
)

# Añadir línea de referencia en 1.0
fig_estacionalidad.add_shape(
    type='line',
    x0=-0.5,
    y0=1,
    x1=11.5,
    y1=1,
    line=dict(color='black', width=1, dash='dash')
)

st.plotly_chart(fig_estacionalidad, use_container_width=True)

# Comparación de períodos si está activada
if comparar_periodos:
    st.header('Comparación de Períodos')
    st.markdown(f"""
    Esta sección compara los KPIs y la distribución de ventas entre dos períodos seleccionados:
    **{MESES[periodo1_mes]} {periodo1_año}** vs **{MESES[periodo2_mes]} {periodo2_año}**.
    Los porcentajes muestran la variación entre ambos períodos.
    """)
    
    # Filtrar datos para los períodos seleccionados
    df_periodo1 = df[(df['anio'] == periodo1_año) & (df['mes'] == periodo1_mes)]
    df_periodo2 = df[(df['anio'] == periodo2_año) & (df['mes'] == periodo2_mes)]
    
    # Calcular KPIs para ambos períodos
    kpi_periodo1 = {
        'valor_total': df_periodo1['valor_total'].sum(),
        'cantidad_total': df_periodo1['cantidad_total'].sum(),
        'clientes_unicos': df_periodo1['cod_clte'].nunique()
    }
    
    kpi_periodo2 = {
        'valor_total': df_periodo2['valor_total'].sum(),
        'cantidad_total': df_periodo2['cantidad_total'].sum(),
        'clientes_unicos': df_periodo2['cod_clte'].nunique()
    }
    
    # Calcular diferencias porcentuales
    diff_valor = ((kpi_periodo2['valor_total'] / kpi_periodo1['valor_total']) - 1) * 100 if kpi_periodo1['valor_total'] > 0 else 0
    diff_cantidad = ((kpi_periodo2['cantidad_total'] / kpi_periodo1['cantidad_total']) - 1) * 100 if kpi_periodo1['cantidad_total'] > 0 else 0
    diff_clientes = ((kpi_periodo2['clientes_unicos'] / kpi_periodo1['clientes_unicos']) - 1) * 100 if kpi_periodo1['clientes_unicos'] > 0 else 0
    
    # Mostrar comparación
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            f"Valor Total",
            f"${kpi_periodo2['valor_total']:,.2f}",
            f"{diff_valor:+.1f}% vs {MESES[periodo1_mes]} {periodo1_año}"
        )
    
    with col2:
        st.metric(
            f"Cantidad Total",
            f"{kpi_periodo2['cantidad_total']:,}",
            f"{diff_cantidad:+.1f}% vs {MESES[periodo1_mes]} {periodo1_año}"
        )
    
    with col3:
        st.metric(
            f"Clientes Únicos",
            f"{kpi_periodo2['clientes_unicos']:,}",
            f"{diff_clientes:+.1f}% vs {MESES[periodo1_mes]} {periodo1_año}"
        )
    
    # Gráfico comparativo de categorías
    cat_periodo1 = df_periodo1.groupby('categoria')['valor_total'].sum().reset_index()
    cat_periodo1['periodo'] = f"{MESES[periodo1_mes]} {periodo1_año}"
    
    cat_periodo2 = df_periodo2.groupby('categoria')['valor_total'].sum().reset_index()
    cat_periodo2['periodo'] = f"{MESES[periodo2_mes]} {periodo2_año}"
    
    # Agrupar categorías pequeñas
    cat_periodo1 = agrupar_pequenos(cat_periodo1, 'categoria', 'valor_total')
    cat_periodo2 = agrupar_pequenos(cat_periodo2, 'categoria', 'valor_total')
    
    cat_comparacion = pd.concat([cat_periodo1, cat_periodo2])
    
    fig_cat_comp = px.bar(
        cat_comparacion,
        x='categoria',
        y='valor_total',
        color='periodo',
        barmode='group',
        title=f'Comparación de Ventas por Categoría: {MESES[periodo1_mes]} {periodo1_año} vs {MESES[periodo2_mes]} {periodo2_año}'
    )
    
    fig_cat_comp.update_layout(
        xaxis_title="Categoría",
        yaxis_title="Valor Total ($)",
        bargap=0.3
    )
    
    st.plotly_chart(fig_cat_comp, use_container_width=True)

# Análisis por Cliente
st.header('Análisis por Cliente')
st.markdown("""
Esta sección muestra los clientes más importantes según su valor total de compras y su frecuencia.
Permite identificar a los clientes VIP y aquellos con patrones de compra específicos.
""")

st.write("Clientes únicos en datos filtrados:", df_filtrado['cod_clte'].nunique())

col1, col2 = st.columns(2)

with col1:
    # Agrupar y unir con nombres
    top_clientes = (
        df_filtrado.groupby('cod_clte')
        .agg({'valor_total': 'sum'})
        .reset_index()
    )
    top_clientes['cod_clte'] = top_clientes['cod_clte'].astype(str)
    top_clientes = top_clientes.merge(df_clientes[['cod_clte', 'nom_clte']], on='cod_clte', how='left')

    top_clientes = top_clientes.sort_values('valor_total', ascending=False).head(5)
    top_clientes['cliente'] = top_clientes['nom_clte'] + ' (' + top_clientes['cod_clte'] + ')'

    if not top_clientes.empty:
        total_ventas = df_filtrado['valor_total'].sum()
        if total_ventas > 0:
            top_clientes['porcentaje'] = top_clientes['valor_total'] / total_ventas * 100

            fig = px.pie(
                top_clientes,
                values='valor_total',
                names='cliente',  # <- usamos la columna combinada
                title='Top 5 Clientes por Participación en Ventas',
                hole=0.4,
                color='valor_total',
                color_discrete_sequence=px.colors.sequential.Blues
            )

            fig.update_traces(
                textinfo='percent+label',
                hovertemplate='<b>Cliente: %{label}</b><br>Valor Total: %{value:$,.2f}<br>Participación: %{percent}',
                textfont_size=14
            )

            st.plotly_chart(fig, use_container_width=True)

            st.markdown("""
            **Interpretación:** Este gráfico muestra la participación porcentual de los 5 clientes más importantes.
            Ideal para entender la concentración de las ventas en pocos clientes clave.
            """)
        else:
            st.warning("No hay ventas en el período seleccionado.")
    else:
        st.warning("No hay suficientes clientes para mostrar el Top 5.")



with col2:
    # Histograma de frecuencia de compra
    frecuencia_distribucion = df_filtrado.groupby('cod_clte')['mes'].nunique().value_counts().sort_index().reset_index()
    frecuencia_distribucion.columns = ['meses_activos', 'n_clientes']

    fig = px.bar(
        frecuencia_distribucion,
        x='meses_activos',
        y='n_clientes',
        title='Distribución de Clientes por Frecuencia de Compra (Meses)',
        text='n_clientes',
        color='n_clientes',
        color_continuous_scale='Purples'
    )

    fig.update_layout(
        bargap=0.2,
        xaxis_title="Meses con Compras",
        yaxis_title="Número de Clientes"
    )

    fig.update_traces(
        textposition='auto',
        textfont_size=14
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Interpretación:** Este gráfico muestra cuántos clientes han comprado en 1, 2, 3... N meses distintos.
    Es útil para entender la distribución general de la frecuencia de compra y detectar oportunidades para aumentar la recurrencia.
    """)

# Segmentación de Clientes (RFM simplificado)
st.header('Segmentación de Clientes')
st.markdown("""
Este análisis segmenta a los clientes según su valor (eje vertical) y frecuencia (eje horizontal).
Permite identificar diferentes perfiles de clientes y desarrollar estrategias específicas para cada segmento:

- **VIP**: Alto valor y alta frecuencia - Clientes estratégicos que requieren atención prioritaria
- **Grandes Ocasionales**: Alto valor pero baja frecuencia - Potencial para aumentar su frecuencia de compra
- **Frecuentes Pequeños**: Bajo valor pero alta frecuencia - Candidatos para estrategias de up-selling
- **Pequeños**: Bajo valor y baja frecuencia - Requieren activación o pueden no ser prioritarios
""")

df_segmentacion = df_filtrado.groupby('cod_clte').agg({
    'valor_total': 'sum',
    'mes': 'nunique',
}).reset_index()
df_segmentacion['cod_clte'] = df_segmentacion['cod_clte'].astype(str)
df_segmentacion = df_segmentacion.merge(df_clientes[['cod_clte', 'nom_clte']], on='cod_clte', how='left')

if not df_segmentacion.empty:
    df_segmentacion['valor_norm'] = df_segmentacion['valor_total'] / df_segmentacion['valor_total'].max()
    df_segmentacion['freq_norm'] = df_segmentacion['mes'] / df_segmentacion['mes'].max()

    df_segmentacion['segmento'] = 'Pequeños'
    df_segmentacion.loc[(df_segmentacion['valor_norm'] >= 0.5) & (df_segmentacion['freq_norm'] >= 0.5), 'segmento'] = 'VIP'
    df_segmentacion.loc[(df_segmentacion['valor_norm'] >= 0.5) & (df_segmentacion['freq_norm'] < 0.5), 'segmento'] = 'Grandes Ocasionales'
    df_segmentacion.loc[(df_segmentacion['valor_norm'] < 0.5) & (df_segmentacion['freq_norm'] >= 0.5), 'segmento'] = 'Frecuentes Pequeños'

    df_segmentacion['valor_total_fmt'] = df_segmentacion['valor_total'].apply(formatear_valor)

    fig_segmentacion = px.scatter(
        df_segmentacion,
        x='freq_norm',
        y='valor_norm',
        color='segmento',
        size='valor_total',
        hover_data={
            'nom_clte': True,
            'valor_total_fmt': True,
            'valor_total': False,
            'mes': True
        },
        title='Segmentación de Clientes por Valor y Frecuencia',
        labels={
            'freq_norm': 'Frecuencia Normalizada',
            'valor_norm': 'Valor Normalizado',
            'segmento': 'Segmento'
        },
        color_discrete_map={
            'VIP': 'green',
            'Grandes Ocasionales': 'blue',
            'Frecuentes Pequeños': 'orange',
            'Pequeños': 'red'
        }
    )

    fig_segmentacion.add_shape(
        type='line',
        x0=0.5, y0=0, x1=0.5, y1=1,
        line=dict(color='gray', width=1, dash='dash')
    )

    fig_segmentacion.add_shape(
        type='line',
        x0=0, y0=0.5, x1=1, y1=0.5,
        line=dict(color='gray', width=1, dash='dash')
    )

    fig_segmentacion.add_annotation(x=0.75, y=0.75, text="VIP", showarrow=False, font=dict(size=14))
    fig_segmentacion.add_annotation(x=0.25, y=0.75, text="Grandes Ocasionales", showarrow=False, font=dict(size=14))
    fig_segmentacion.add_annotation(x=0.75, y=0.25, text="Frecuentes Pequeños", showarrow=False, font=dict(size=14))
    fig_segmentacion.add_annotation(x=0.25, y=0.25, text="Pequeños", showarrow=False, font=dict(size=14))

    st.plotly_chart(fig_segmentacion, use_container_width=True)
else:
    st.warning("No hay suficientes datos para la segmentación de clientes con los filtros actuales.")


# Tasa de Penetración en el Mercado
st.header('Tasa de Penetración en el Mercado')
st.markdown("""
Este gráfico muestra el porcentaje de clientes que compran cada categoría de productos.
Una alta penetración indica que la categoría es popular entre los clientes, mientras que una baja penetración
puede representar una oportunidad de crecimiento o un nicho específico.
""")

# Calcular penetración por categoría
total_clientes = df_filtrado['cod_clte'].nunique()
penetracion_categorias = df_filtrado.groupby('categoria')['cod_clte'].nunique().reset_index()
penetracion_categorias.columns = ['categoria', 'clientes']
penetracion_categorias['penetracion'] = penetracion_categorias['clientes'] / total_clientes * 100

# Agrupar categorías pequeñas
penetracion_categorias = agrupar_pequenos(penetracion_categorias, 'categoria', 'penetracion')

# Crear gráfico de penetración
fig_penetracion = px.bar(
    penetracion_categorias,
    y='categoria',
    x='penetracion',
    title='Tasa de Penetración por Categoría (% de Clientes)',
    orientation='h',
    text=penetracion_categorias['penetracion'].apply(lambda x: f"{x:.1f}%"),
    color='penetracion',
    color_continuous_scale='Viridis'
)

fig_penetracion.update_layout(
    xaxis_title="% de Clientes",
    yaxis_title="Categoría",
    yaxis={'categoryorder':'total ascending'}
)

fig_penetracion.update_traces(
    textposition='auto',
    textfont_size=12,
    width=0.7  # Barras más anchas
)

st.plotly_chart(fig_penetracion, use_container_width=True)

# Análisis por Producto
st.header('Análisis por Producto')
st.markdown("""
Esta sección muestra los productos más vendidos por cantidad y por valor total.
Permite identificar los productos estrella y aquellos que generan mayor ingreso.
""")

col1, col2 = st.columns(2)

with col1:
    # Top productos por cantidad
    top_productos = df_filtrado.groupby(['art_codi', 'art_desc']).agg({
        'cantidad_total': 'sum'
    }).sort_values('cantidad_total', ascending=False).head(10).reset_index()
    
    # Agrupar productos pequeños si es necesario
    if len(top_productos) > 0:
        total_cantidad = top_productos['cantidad_total'].sum()
        top_productos['porcentaje'] = top_productos['cantidad_total'] / total_cantidad * 100
    
    fig = px.bar(
        top_productos,
        y='art_desc',
        x='cantidad_total',
        title='Top 10 Productos Más Vendidos por Cantidad',
        orientation='h',
        text=top_productos['cantidad_total'].apply(lambda x: f"{x:,}"),
        color='cantidad_total',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        xaxis_title="Cantidad Total",
        yaxis_title="Producto",
        yaxis={'categoryorder':'total ascending'},
        bargap=0.3
    )
    
    fig.update_traces(
        textposition='auto',
        textfont_size=12,
        width=0.7  # Barras más anchas
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    **Interpretación:** Este gráfico muestra los productos más vendidos por cantidad.
    Estos productos tienen alta rotación y son clave para mantener el volumen de ventas.
    """)

with col2:
    # Productos por valor total
    top_productos_valor = df_filtrado.groupby(['art_codi', 'art_desc']).agg({
        'valor_total': 'sum'
    }).sort_values('valor_total', ascending=False).head(10).reset_index()
    
    # Agrupar productos pequeños si es necesario
    if len(top_productos_valor) > 0:
        total_valor = top_productos_valor['valor_total'].sum()
        top_productos_valor['porcentaje'] = top_productos_valor['valor_total'] / total_valor * 100
    
    fig = px.bar(
        top_productos_valor,
        y='art_desc',
        x='valor_total',
        title='Top 10 Productos por Valor Total',
        orientation='h',
        text=top_productos_valor['valor_total'].apply(lambda x: f"${x:,.2f}"),
        color='valor_total',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        xaxis_title="Valor Total ($)",
        yaxis_title="Producto",
        yaxis={'categoryorder':'total ascending'},
        bargap=0.3
    )
    
    fig.update_traces(
        textposition='auto',
        textfont_size=12,
        width=0.7  # Barras más anchas
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    **Interpretación:** Este gráfico muestra los productos que generan mayor valor en ventas.
    Estos productos son estratégicos para la rentabilidad del negocio, aunque no necesariamente
    sean los más vendidos por cantidad.
    """)

# Análisis por Categoría con Drill-down
st.header('Análisis por Categoría')
st.markdown("""
Esta sección permite analizar la distribución de ventas por categoría y profundizar en el detalle
de subcategorías y productos específicos de cada categoría seleccionada.
""")

# Selector de categoría para drill-down
categoria_seleccionada = st.selectbox(
    "Seleccionar Categoría para Ver Detalle",
    ["Todas"] + list(df_filtrado['categoria'].unique())
)

col1, col2 = st.columns(2)

with col1:
    # Categorías
    if categoria_seleccionada == "Todas":
        categorias = df_filtrado.groupby('categoria').agg({
            'valor_total': 'sum'
        }).reset_index()
        
        # Agrupar categorías pequeñas
        categorias = agrupar_pequenos(categorias, 'categoria', 'valor_total')
        
        fig = px.pie(
            categorias,
            values='valor_total',
            names='categoria',
            title='Distribución de Ventas por Categoría',
            hole=0.4
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            insidetextfont=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Interpretación:** Este gráfico muestra la distribución porcentual de las ventas por categoría.
        Las categorías con mayor porcentaje representan las áreas de negocio más importantes.
        """)
    else:
        # Mostrar subcategorías de la categoría seleccionada
        subcategorias_filtradas = df_filtrado[df_filtrado['categoria'] == categoria_seleccionada]
        subcategorias = subcategorias_filtradas.groupby('subcategoria').agg({
            'valor_total': 'sum'
        }).reset_index()
        
        # Agrupar subcategorías pequeñas
        subcategorias = agrupar_pequenos(subcategorias, 'subcategoria', 'valor_total')
        
        fig = px.pie(
            subcategorias,
            values='valor_total',
            names='subcategoria',
            title=f'Distribución de Ventas en Categoría: {categoria_seleccionada}',
            hole=0.4
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            insidetextfont=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"""
        **Interpretación:** Este gráfico muestra la distribución de ventas dentro de la categoría **{categoria_seleccionada}**.
        Permite identificar las subcategorías más relevantes dentro de esta línea de productos.
        """)

with col2:
    # Subcategorías o productos según selección
    if categoria_seleccionada == "Todas":
        # Subcategorías generales
        subcategorias = df_filtrado.groupby('subcategoria').agg({
            'valor_total': 'sum'
        }).reset_index()
        
        # Agrupar subcategorías pequeñas
        subcategorias = agrupar_pequenos(subcategorias, 'subcategoria', 'valor_total')
        
        fig = px.treemap(
            subcategorias,
            path=['subcategoria'],
            values='valor_total',
            title='Distribución de Ventas por Subcategoría',
            color='valor_total',
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Interpretación:** Este mapa de árbol muestra la distribución de ventas por subcategoría.
        El tamaño de cada rectángulo representa el valor de ventas, permitiendo identificar
        visualmente las subcategorías más importantes.
        """)
    else:
        # Mostrar productos de la categoría seleccionada
        productos_categoria = df_filtrado[df_filtrado['categoria'] == categoria_seleccionada]
        productos = productos_categoria.groupby('art_desc').agg({
            'valor_total': 'sum'
        }).sort_values('valor_total', ascending=False).head(10).reset_index()
        
        fig = px.bar(
            productos,
            y='art_desc',
            x='valor_total',
            title=f'Top 10 Productos en Categoría: {categoria_seleccionada}',
            orientation='h',
            text=productos['valor_total'].apply(lambda x: f"${x:,.2f}"),
            color='valor_total',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="Valor Total ($)",
            yaxis_title="Producto",
            bargap=0.3
        )
        
        fig.update_traces(
            textposition='auto',
            textfont_size=12,
            width=0.7  # Barras más anchas
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"""
        **Interpretación:** Este gráfico muestra los productos más vendidos dentro de la categoría **{categoria_seleccionada}**.
        Permite identificar qué productos específicos están impulsando las ventas en esta categoría.
        """)

# Resumen y conclusiones
st.header('Resumen y Conclusiones')
st.markdown("""
Este dashboard proporciona una visión completa del rendimiento de ventas, permitiendo:

1. **Monitorear KPIs clave** como valor total, cantidad vendida y ticket promedio.
2. **Analizar tendencias temporales** para identificar patrones estacionales y oportunidades.
3. **Segmentar clientes** según su valor y frecuencia para estrategias personalizadas.
4. **Identificar productos estrella** tanto por cantidad como por valor.
5. **Explorar categorías en detalle** mediante análisis drill-down.
6. **Comparar períodos específicos** para evaluar el crecimiento.

Las decisiones basadas en estos datos pueden ayudar a optimizar inventarios, mejorar estrategias de marketing,
personalizar la atención al cliente y maximizar la rentabilidad del negocio.
""")