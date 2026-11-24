import numpy as np
import pandas as pd

from src.rutas import LIGAS

# Fechas que separan los periodos del análisis
INICIO_COVID = pd.Timestamp("2020-03-08")       # primeros partidos a puerta cerrada (Serie A)
FIN_RESTRICCIONES = pd.Timestamp("2022-07-01")  # desde la temporada 2022-23 no hay restricciones
UMBRAL_AFORO_COMPLETO = 0.75                    # asistencia >= 75 % de lo habitual = público completo

ORDEN_PERIODOS = ["Antes del COVID", "Sin público", "Aforo parcial", "Regreso del público"]


def construir_equivalencias(df_fd: pd.DataFrame, df_tm: pd.DataFrame) -> pd.DataFrame:
    """
    Las dos fuentes escriben distinto los nombres de los equipos
    (p. ej. 'Man City' vs 'Manchester City Football Club').
    Para encontrar la equivalencia se cruzan los partidos de la misma liga, el mismo día
    y con el mismo marcador; el nombre de Transfermarkt que más veces coincide con cada
    nombre de football-data se toma como su equivalente.
    """
    if df_fd.empty or df_tm.empty:
        return pd.DataFrame()

    llaves = ["liga", "fecha", "goles_local", "goles_visitante"]
    tm = df_tm.rename(columns={"goles_local_tm": "goles_local", "goles_visitante_tm": "goles_visitante"})
    cruce = df_fd[llaves + ["local", "visitante"]].merge(
        tm[llaves + ["local_tm", "visitante_tm"]], on=llaves, how="inner"
    )

    # Cada partido cruzado aporta dos parejas de nombres: la del local y la del visitante
    parejas_local = cruce[["liga", "local", "local_tm"]].set_axis(["liga", "equipo_fd", "equipo_tm"], axis=1)
    parejas_visita = cruce[["liga", "visitante", "visitante_tm"]].set_axis(["liga", "equipo_fd", "equipo_tm"], axis=1)
    parejas = pd.concat([parejas_local, parejas_visita])

    conteo = parejas.value_counts().reset_index(name="coincidencias")
    conteo = conteo.sort_values("coincidencias", ascending=False)
    equivalencias = conteo.drop_duplicates(subset=["liga", "equipo_fd"])

    # Verificación: un nombre de Transfermarkt no puede quedar asignado a dos equipos
    repetidos = equivalencias.duplicated(subset=["liga", "equipo_tm"]).sum()
    if repetidos > 0:
        print(f"Advertencia: {repetidos} nombres de Transfermarkt quedaron asignados a dos equipos.")

    return equivalencias.sort_values(["liga", "equipo_fd"]).reset_index(drop=True)


def agregar_resultados_partido(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega el resultado, los puntos y la diferencia de goles desde el punto de vista del local.
    """
    condiciones = [
        df["goles_local"] > df["goles_visitante"],
        df["goles_local"] < df["goles_visitante"],
    ]
    df["resultado"] = np.select(condiciones, ["Gana local", "Gana visitante"], default="Empate")
    df["puntos_local"] = np.select(condiciones, [3, 0], default=1)
    df["puntos_visitante"] = np.select(condiciones, [0, 3], default=1)
    df["diferencia_goles"] = df["goles_local"] - df["goles_visitante"]
    return df


def clasificar_periodo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica cada partido en un periodo según la fecha, la asistencia (Transfermarkt)
    y las restricciones del país (OxCGRT):
      - Antes del COVID: antes del 8 de marzo de 2020.
      - Sin público: entre marzo de 2020 y junio de 2022, sin asistencia registrada
        y con restricciones a eventos públicos en el país.
      - Aforo parcial: en ese mismo lapso, con asistencia menor al 75 % de la habitual del estadio.
      - Regreso del público: asistencia de nuevo en niveles normales o partidos desde julio de 2022.
    """
    # Asistencia habitual de cada local = mediana en fechas normales (sin COVID)
    fechas_normales = (df["fecha"] < INICIO_COVID) | (df["fecha"] >= FIN_RESTRICCIONES)
    habitual = df[fechas_normales].groupby("local")["asistencia"].median()
    maxima = df.groupby("local")["asistencia"].max()  # respaldo para equipos sin fechas normales
    df["asistencia_habitual"] = df["local"].map(habitual).fillna(df["local"].map(maxima))
    df["ocupacion_relativa"] = (df["asistencia"] / df["asistencia_habitual"]).round(3)

    en_covid = (df["fecha"] >= INICIO_COVID) & (df["fecha"] < FIN_RESTRICCIONES)
    sin_asistencia = df["asistencia"].isna() | (df["asistencia"] == 0)

    condiciones = [
        df["fecha"] < INICIO_COVID,
        en_covid & sin_asistencia & (df["restriccion_eventos"] >= 1),
        en_covid & sin_asistencia,
        en_covid & (df["ocupacion_relativa"] < UMBRAL_AFORO_COMPLETO),
    ]
    periodos = ["Antes del COVID", "Sin público", "Sin dato", "Aforo parcial"]
    df["periodo"] = np.select(condiciones, periodos, default="Regreso del público")
    return df


def integrar_fuentes(df_fd: pd.DataFrame, df_tm: pd.DataFrame, df_ox: pd.DataFrame,
                     equivalencias: pd.DataFrame) -> tuple:
    """
    Une las tres fuentes en una tabla con una fila por partido.
    Retorna (tabla_integrada, reporte_de_integracion).
    """
    reporte = []

    def anotar(paso: str, valor, detalle: str = "") -> None:
        reporte.append({"paso": paso, "valor": valor, "detalle": detalle})

    anotar("Partidos en football-data", len(df_fd), "Fuente 1, una fila por partido")
    anotar("Partidos en Transfermarkt", len(df_tm), "Fuente 2, mismas ligas y temporadas")
    anotar("Días-país en OxCGRT", len(df_ox), "Fuente 3, 5 países, 2020-01-01 a 2022-12-31")
    anotar("Equipos con equivalencia de nombre", len(equivalencias),
           "Nombres football-data -> Transfermarkt (ver equivalencias_equipos.csv)")

    # --- Unión 1: football-data + Transfermarkt (liga + fecha + local + visitante) ---
    mapa = equivalencias[["liga", "equipo_fd", "equipo_tm"]]
    df = df_fd.merge(mapa.rename(columns={"equipo_fd": "local", "equipo_tm": "local_tm"}),
                     on=["liga", "local"], how="left")
    df = df.merge(mapa.rename(columns={"equipo_fd": "visitante", "equipo_tm": "visitante_tm"}),
                  on=["liga", "visitante"], how="left")

    duplicados_tm = df_tm.duplicated(subset=["liga", "fecha", "local_tm", "visitante_tm"]).sum()
    anotar("Duplicados en Transfermarkt", int(duplicados_tm), "Partidos repetidos con la misma llave")

    df = df.merge(df_tm, on=["liga", "fecha", "local_tm", "visitante_tm"], how="left",
                  validate="one_to_one", indicator=True)
    sin_tm = (df["_merge"] == "left_only").sum()
    anotar("Partidos unidos football-data + Transfermarkt", int((df["_merge"] == "both").sum()),
           "Cardinalidad 1 a 1 verificada")
    anotar("Partidos de football-data sin pareja en Transfermarkt", int(sin_tm),
           "Se conservan; quedan sin asistencia ni árbitro")
    anotar("Partidos de Transfermarkt sin pareja en football-data", int(len(df_tm) - (df["_merge"] == "both").sum()),
           "Se descartan")

    marcador_distinto = ((df["_merge"] == "both") &
                         ((df["goles_local"] != df["goles_local_tm"]) |
                          (df["goles_visitante"] != df["goles_visitante_tm"]))).sum()
    anotar("Partidos unidos con marcador distinto", int(marcador_distinto), "Control de calidad de la unión")
    df = df.drop(columns=["_merge", "goles_local_tm", "goles_visitante_tm"])

    # --- Unión 2: + OxCGRT (país de la liga + fecha) ---
    df["pais"] = df["liga"].map({nombre: pais for nombre, (_, _, pais) in LIGAS.items()})
    df = df.merge(df_ox, on=["pais", "fecha"], how="left", validate="many_to_one")
    fuera_cobertura = df["indice_rigurosidad"].isna().sum()
    anotar("Partidos fuera de la cobertura de OxCGRT", int(fuera_cobertura),
           "Antes de 2020 o después de 2022: no había restricciones, se asigna 0")
    for columna in ["restriccion_eventos", "restriccion_reuniones", "indice_rigurosidad"]:
        df[columna] = df[columna].fillna(0)

    # --- Variables construidas ---
    df = agregar_resultados_partido(df)
    df = clasificar_periodo(df)

    for periodo, cantidad in df["periodo"].value_counts().items():
        anotar(f"Partidos en periodo '{periodo}'", int(cantidad))

    sin_dato = df["periodo"] == "Sin dato"
    df = df[~sin_dato].reset_index(drop=True)
    anotar("Partidos finales en el dashboard", len(df),
           "Se excluyen los 'Sin dato' (sin asistencia y sin restricciones: dato faltante)")

    return df, pd.DataFrame(reporte)
