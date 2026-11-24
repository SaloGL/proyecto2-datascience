import pandas as pd

from src.rutas import (
    CARPETA_FOOTBALL_DATA, ARCHIVO_TRANSFERMARKT, ARCHIVO_OXCGRT, ARCHIVO_PARTIDOS,
    LIGAS, TEMPORADAS
)


def validar_columnas(df: pd.DataFrame, columnas_requeridas: list, nombre: str) -> None:
    """
    Lanza un ValueError si alguna columna obligatoria no está en el DataFrame.
    """
    for columna in columnas_requeridas:
        if columna not in df.columns:
            raise ValueError(f"Error: la columna '{columna}' no está en {nombre}.")


def cargar_football_data() -> pd.DataFrame:
    """
    Fuente 1. Une los CSV de todas las ligas y temporadas de football-data.co.uk
    y deja un DataFrame limpio con una fila por partido.
    """
    columnas_requeridas = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
                           "HS", "AS", "HST", "AST", "HF", "AF", "HY", "AY", "HR", "AR"]
    tablas = []

    for nombre_liga, (carpeta_liga, _, _) in LIGAS.items():
        for temporada in TEMPORADAS:
            ruta = CARPETA_FOOTBALL_DATA / f"{carpeta_liga}_{temporada}.csv"
            if not ruta.exists():
                print(f"Advertencia: falta el archivo {ruta.name}. Ejecuta 'python main.py'.")
                continue
            tabla = pd.read_csv(ruta)
            validar_columnas(tabla, columnas_requeridas, ruta.name)
            tabla["liga"] = nombre_liga
            tabla["temporada"] = f"20{temporada[:2]}-{temporada[2:]}"
            tablas.append(tabla)

    if not tablas:
        return pd.DataFrame()

    df = pd.concat(tablas, ignore_index=True)

    # Nombres en español para que el resto del código sea fácil de leer
    df = df.rename(columns={
        "Date": "fecha", "HomeTeam": "local", "AwayTeam": "visitante",
        "FTHG": "goles_local", "FTAG": "goles_visitante",
        "HS": "tiros_local", "AS": "tiros_visitante",
        "HST": "tiros_puerta_local", "AST": "tiros_puerta_visitante",
        "HF": "faltas_local", "AF": "faltas_visitante",
        "HY": "amarillas_local", "AY": "amarillas_visitante",
        "HR": "rojas_local", "AR": "rojas_visitante",
    })

    # Limpieza básica
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["local"] = df["local"].str.strip()
    df["visitante"] = df["visitante"].str.strip()
    df = df.dropna(subset=["fecha", "local", "visitante", "goles_local", "goles_visitante"])
    df = df.drop_duplicates(subset=["liga", "fecha", "local", "visitante"])

    columnas = ["liga", "temporada", "fecha", "local", "visitante", "goles_local", "goles_visitante",
                "tiros_local", "tiros_visitante", "tiros_puerta_local", "tiros_puerta_visitante",
                "faltas_local", "faltas_visitante", "amarillas_local", "amarillas_visitante",
                "rojas_local", "rojas_visitante"]
    return df[columnas]


def cargar_transfermarkt() -> pd.DataFrame:
    """
    Fuente 2. Lee los partidos de Transfermarkt y se queda con las cinco ligas
    y las temporadas analizadas. Aporta asistencia, estadio y árbitro.
    """
    if not ARCHIVO_TRANSFERMARKT.exists():
        print(f"Error: no existe {ARCHIVO_TRANSFERMARKT}. Ejecuta 'python main.py'.")
        return pd.DataFrame()

    df = pd.read_csv(ARCHIVO_TRANSFERMARKT)
    validar_columnas(df, ["competition_id", "date", "home_club_name", "away_club_name",
                          "home_club_goals", "away_club_goals", "attendance", "referee",
                          "stadium"], "Transfermarkt")

    # Código de competición -> nombre de la liga
    codigo_a_liga = {codigo: nombre for nombre, (_, codigo, _) in LIGAS.items()}
    df = df[df["competition_id"].isin(codigo_a_liga.keys())].copy()
    df["liga"] = df["competition_id"].map(codigo_a_liga)

    df["fecha"] = pd.to_datetime(df["date"], errors="coerce")
    primera_fecha = pd.Timestamp(f"20{TEMPORADAS[0][:2]}-07-01")
    ultima_fecha = pd.Timestamp(f"20{TEMPORADAS[-1][2:]}-07-01")
    df = df[(df["fecha"] >= primera_fecha) & (df["fecha"] < ultima_fecha)]

    df = df.rename(columns={
        "home_club_name": "local_tm", "away_club_name": "visitante_tm",
        "home_club_goals": "goles_local_tm", "away_club_goals": "goles_visitante_tm",
        "attendance": "asistencia", "referee": "arbitro", "stadium": "estadio",
    })
    df["local_tm"] = df["local_tm"].str.strip()
    df["visitante_tm"] = df["visitante_tm"].str.strip()
    df["arbitro"] = df["arbitro"].str.strip()

    columnas = ["liga", "fecha", "local_tm", "visitante_tm", "goles_local_tm", "goles_visitante_tm",
                "asistencia", "arbitro", "estadio"]
    return df[columnas].reset_index(drop=True)


def cargar_oxcgrt() -> pd.DataFrame:
    """
    Fuente 3. Lee el Oxford COVID-19 Government Response Tracker y se queda con
    los cinco países de las ligas. Una fila por país y día.
    """
    if not ARCHIVO_OXCGRT.exists():
        print(f"Error: no existe {ARCHIVO_OXCGRT}. Ejecuta 'python main.py'.")
        return pd.DataFrame()

    columnas_usadas = ["CountryCode", "Jurisdiction", "Date", "C3M_Cancel public events",
                       "C4M_Restrictions on gatherings", "StringencyIndex_Average"]
    df = pd.read_csv(ARCHIVO_OXCGRT, usecols=columnas_usadas)

    paises = [pais for (_, _, pais) in LIGAS.values()]
    df = df[df["CountryCode"].isin(paises) & (df["Jurisdiction"] == "NAT_TOTAL")].copy()

    df = df.rename(columns={
        "CountryCode": "pais", "C3M_Cancel public events": "restriccion_eventos",
        "C4M_Restrictions on gatherings": "restriccion_reuniones",
        "StringencyIndex_Average": "indice_rigurosidad",
    })
    df["fecha"] = pd.to_datetime(df["Date"].astype(str), format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["fecha"]).drop_duplicates(subset=["pais", "fecha"])

    return df[["pais", "fecha", "restriccion_eventos", "restriccion_reuniones", "indice_rigurosidad"]]


def cargar_partidos_integrados() -> pd.DataFrame:
    """
    Carga la tabla final (datos/procesados) que alimenta el dashboard.
    """
    if not ARCHIVO_PARTIDOS.exists():
        print(f"Error: no existe {ARCHIVO_PARTIDOS}. Ejecuta primero 'python main.py'.")
        return pd.DataFrame()

    df = pd.read_csv(ARCHIVO_PARTIDOS, parse_dates=["fecha"])
    return df
