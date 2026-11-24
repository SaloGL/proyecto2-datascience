import streamlit as st
import pandas as pd

from src.rutas import ARCHIVO_REPORTE
from src.cargador import cargar_partidos_integrados
from src.integrador import ORDEN_PERIODOS
from src.estadisticas import filtrar_partidos, resumen_por_periodo, serie_mensual, generar_hallazgos
from src.visualizador import (
    graficar_resultados_por_periodo, graficar_ventaja_por_periodo,
    graficar_evolucion_mensual
)

# Configuración de la página
st.set_page_config(page_title="Ventaja de local y público", layout="wide")


@st.cache_data
def cargar_datos():
    return cargar_partidos_integrados()


df_partidos = cargar_datos()

if df_partidos.empty:
    st.error("No se encontraron los datos procesados. Ejecuta primero en la terminal:  python main.py")
    st.stop()

# ==========================================
# ENCABEZADO: la pregunta del proyecto
# ==========================================
st.title("¿Cuánto de la ventaja de jugar en casa se debe al público?")
st.info(
    "**Pregunta analítica:** ¿cómo cambiaron el rendimiento del local y las decisiones arbitrales "
    "antes, durante y después de los partidos sin público por el COVID (2020-2021) en las cinco grandes "
    "ligas europeas?  \n"
    "Los partidos a puerta cerrada son un **experimento natural**: el mismo fútbol, los mismos equipos, "
    "pero sin afición en las tribunas."
)

# ==========================================
# BARRA LATERAL: filtros
# ==========================================
st.sidebar.header("Filtros")

ligas = st.sidebar.multiselect("Liga", sorted(df_partidos["liga"].unique()),
                               default=sorted(df_partidos["liga"].unique()))

todas_temporadas = sorted(df_partidos["temporada"].unique())
temporada_inicio, temporada_fin = st.sidebar.select_slider(
    "Temporadas", options=todas_temporadas, value=(todas_temporadas[0], todas_temporadas[-1])
)
temporadas = [t for t in todas_temporadas if temporada_inicio <= t <= temporada_fin]

periodos = st.sidebar.multiselect("Periodo", ORDEN_PERIODOS, default=ORDEN_PERIODOS)

partidos_liga = df_partidos[df_partidos["liga"].isin(ligas)]
equipos = ["Todos"] + sorted(partidos_liga["local"].unique())
equipo = st.sidebar.selectbox("Equipo", equipos)
condicion = st.sidebar.radio("Condición del equipo", ["Local o visitante", "Solo como local", "Solo como visitante"],
                             disabled=(equipo == "Todos"))

arbitros = ["Todos"] + partidos_liga["arbitro"].value_counts().index.tolist()
arbitro = st.sidebar.selectbox("Árbitro (ordenados por partidos dirigidos)", arbitros)

st.sidebar.caption("Todos los indicadores se miden desde el punto de vista del equipo **local**.")

df_filtrado = filtrar_partidos(df_partidos, ligas, temporadas, periodos, equipo, condicion, arbitro)

if df_filtrado.empty:
    st.warning("No hay partidos con esa combinación de filtros. Prueba con otros.")
    st.stop()

resumen = resumen_por_periodo(df_filtrado)

# ==========================================
# INDICADORES PRINCIPALES
# ==========================================
st.subheader("Indicadores principales: con público vs sin público")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Partidos analizados", f"{len(df_filtrado):,}".replace(",", "."))

if "Antes del COVID" in resumen.index and "Sin público" in resumen.index:
    antes = resumen.loc["Antes del COVID"]
    sin = resumen.loc["Sin público"]
    col2.metric("Victorias del local sin público", f"{sin['pct_gana_local']:.1f} %",
                f"{sin['pct_gana_local'] - antes['pct_gana_local']:+.1f} pp vs con público")
    col3.metric("Ventaja de puntos por partido sin público", f"{sin['ventaja_puntos']:+.2f}",
                f"{sin['ventaja_puntos'] - antes['ventaja_puntos']:+.2f} vs con público")
    col4.metric("Amarillas extra al visitante sin público", f"{sin['sesgo_amarillas']:+.2f}",
                f"{sin['sesgo_amarillas'] - antes['sesgo_amarillas']:+.2f} vs con público")
else:
    col2.info("Incluye los periodos 'Antes del COVID' y 'Sin público' para ver la comparación.")

# ==========================================
# 1. RESULTADOS
# ==========================================
st.subheader("1. ¿Cómo terminan los partidos en cada periodo?")
fig = graficar_resultados_por_periodo(resumen)
if fig:
    st.pyplot(fig)

# ==========================================
# 2. VENTAJA DEL LOCAL
# ==========================================
st.subheader("2. Ventaja del local sobre el visitante (local − visitante, promedio por partido)")
col1, col2, col3 = st.columns(3)
for columna, (indicador, titulo) in zip(
    [col1, col2, col3],
    [("ventaja_puntos", "Puntos"), ("ventaja_goles", "Goles"), ("ventaja_tiros_puerta", "Tiros a puerta")]
):
    fig = graficar_ventaja_por_periodo(resumen, indicador, titulo)
    if fig:
        columna.pyplot(fig)
st.caption("Un valor positivo significa que el local supera al visitante. Mientras más cerca de 0, menor es la ventaja de jugar en casa.")

# ==========================================
# 3. ARBITRAJE
# ==========================================
st.subheader("3. ¿Cambia el arbitraje sin la presión del público? (visitante − local, promedio por partido)")
col1, col2, col3 = st.columns(3)
for columna, (indicador, titulo) in zip(
    [col1, col2, col3],
    [("sesgo_amarillas", "Tarjetas amarillas"), ("sesgo_faltas", "Faltas pitadas"), ("sesgo_rojas", "Tarjetas rojas")]
):
    fig = graficar_ventaja_por_periodo(resumen, indicador, titulo)
    if fig:
        columna.pyplot(fig)
st.caption("Un valor positivo significa que el árbitro sanciona más al visitante que al local. Si la brecha se cierra "
           "sin público, parte de esa diferencia se explica por la presión de la grada sobre el árbitro.")

# ==========================================
# 4. EVOLUCIÓN EN EL TIEMPO
# ==========================================
st.subheader("4. Evolución mes a mes")
fig = graficar_evolucion_mensual(serie_mensual(df_filtrado))
if fig:
    st.pyplot(fig)
else:
    st.info("Hay muy pocos partidos por mes con estos filtros (se necesitan al menos 10). Amplía la selección para ver la evolución.")
st.caption("Línea: ventaja de puntos del local. Barras grises: ocupación de los estadios frente a su asistencia habitual. "
           "Zona roja: meses con estadios vacíos.")

# ==========================================
# HALLAZGOS, RECOMENDACIONES Y LIMITACIONES
# ==========================================
col1, col2 = st.columns(2)
with col1:
    st.subheader("Hallazgos")
    for hallazgo in generar_hallazgos(resumen):
        st.markdown(f"- {hallazgo}")

with col2:
    st.subheader("Recomendaciones para el comité")
    st.markdown(
        "- **Puertas cerradas como sanción:** sí perjudican al local; le quitan gran parte de su ventaja "
        "deportiva, por lo que es una sanción con efecto real.\n"
        "- **Aforo y restricciones sanitarias:** el público es un factor competitivo. Si se limita el aforo, "
        "conviene hacerlo de forma pareja para todos los equipos de la liga.\n"
        "- **Imparcialidad arbitral:** la diferencia de tarjetas entre local y visitante cambia con el público. "
        "Se recomienda reforzar la formación de árbitros frente a la presión de la grada y el uso del VAR."
    )

st.warning(
    "**Limitaciones de los datos**  \n"
    "- **No es un experimento perfecto:** en el mismo periodo cambiaron otras cosas (cinco cambios por partido, "
    "calendario comprimido, VAR en años distintos según la liga).  \n"
    "- **Tamaño de muestra:** el periodo sin público tiene unos 2.100 partidos, frente a casi 5.000 antes del COVID; "
    "al filtrar por equipo o árbitro las diferencias pueden deberse al azar.  \n"
    "- **Asistencia aproximada:** Transfermarkt no reporta el 0; un partido sin asistencia registrada se toma como "
    "sin público solo si OxCGRT indica restricciones a eventos públicos en el país. El 'aforo parcial' se define como "
    "menos del 75 % de la asistencia habitual del estadio.  \n"
    "- **Árbitro:** football-data solo trae el árbitro de la Premier League; para las demás ligas se usa el de Transfermarkt."
)

# ==========================================
# FUENTES E INTEGRACIÓN
# ==========================================
with st.expander("Fuentes de datos y cómo se integraron"):
    st.markdown(
        "| # | Fuente | Qué aporta | Unidad | Cobertura | Licencia |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | [football-data.co.uk](https://www.football-data.co.uk) (espejo [datasets/football-datasets](https://github.com/datasets/football-datasets)) "
        "| Resultados, tiros, faltas y tarjetas | Partido | 2017-18 a 2023-24 | PDDL (dominio público) |\n"
        "| 2 | [Transfermarkt](https://www.kaggle.com/datasets/davidcariboo/player-scores) (dcaribou) "
        "| Asistencia, estadio y árbitro | Partido | 2017-18 a 2023-24 | CC0 |\n"
        "| 3 | [Oxford COVID-19 Government Response Tracker](https://github.com/OxCGRT/covid-policy-dataset) "
        "| Restricciones a eventos públicos | País-día | 2020-2022 | CC BY 4.0 |\n\n"
        "**Unión 1:** football-data + Transfermarkt por liga + fecha + equipo local + equipo visitante. "
        "Como los nombres de los equipos se escriben distinto, primero se construyó una tabla de equivalencias "
        "cruzando partidos del mismo día con el mismo marcador.  \n"
        "**Unión 2:** + OxCGRT por país de la liga + fecha del partido."
    )
    if ARCHIVO_REPORTE.exists():
        st.write("**Verificación de la integración** (cardinalidad, registros sin correspondencia y duplicados):")
        st.dataframe(pd.read_csv(ARCHIVO_REPORTE), hide_index=True, width="stretch")

with st.expander("Tabla de indicadores por periodo"):
    st.dataframe(resumen.round(2), width="stretch")

with st.expander("Partidos filtrados"):
    columnas = ["liga", "temporada", "fecha", "local", "visitante", "goles_local", "goles_visitante",
                "periodo", "asistencia", "arbitro", "amarillas_local", "amarillas_visitante"]
    st.dataframe(df_filtrado[columnas].sort_values("fecha", ascending=False), hide_index=True,
                 width="stretch")
