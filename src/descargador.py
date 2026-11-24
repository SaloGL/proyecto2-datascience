import urllib.request
from pathlib import Path

from src.rutas import (
    CARPETA_FOOTBALL_DATA, ARCHIVO_TRANSFERMARKT, ARCHIVO_OXCGRT, LIGAS, TEMPORADAS
)

# Fuente 1: resultados y estadísticas por partido de football-data.co.uk.
# Se usa el espejo público de GitHub (datasets/football-datasets) porque la página
# original está bloqueada en algunas redes de Colombia (es un sitio de apuestas).
URL_FOOTBALL_DATA = "https://raw.githubusercontent.com/datasets/football-datasets/main/datasets/{liga}/season-{temporada}.csv"

# Fuente 2: partidos de Transfermarkt (asistencia, estadio, árbitro).
# Es el mismo archivo 'games.csv' del dataset de Kaggle 'player-scores' (davidcariboo).
URL_TRANSFERMARKT = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/games.csv.gz"

# Fuente 3: Oxford COVID-19 Government Response Tracker (restricciones por país y día).
URL_OXCGRT = "https://raw.githubusercontent.com/OxCGRT/covid-policy-dataset/main/data/OxCGRT_compact_national_v1.csv"


def descargar_archivo(url: str, destino: Path, forzar: bool = False) -> bool:
    """
    Descarga un archivo si todavía no existe en la carpeta de datos.
    Retorna True si el archivo quedó disponible.
    """
    if destino.exists() and not forzar:
        print(f"Ya existe: {destino.name}")
        return True

    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(peticion, timeout=120) as respuesta:
            destino.write_bytes(respuesta.read())
        print(f"Descargado: {destino.name}")
        return True
    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return False


def descargar_todo(forzar: bool = False) -> None:
    """
    Descarga las tres fuentes en datos/raw. Los archivos se guardan sin modificar.
    """
    print("--- Fuente 1: football-data.co.uk ---")
    for nombre_liga, (carpeta_liga, _, _) in LIGAS.items():
        for temporada in TEMPORADAS:
            url = URL_FOOTBALL_DATA.format(liga=carpeta_liga, temporada=temporada)
            destino = CARPETA_FOOTBALL_DATA / f"{carpeta_liga}_{temporada}.csv"
            descargar_archivo(url, destino, forzar)

    print("--- Fuente 2: Transfermarkt ---")
    descargar_archivo(URL_TRANSFERMARKT, ARCHIVO_TRANSFERMARKT, forzar)

    print("--- Fuente 3: OxCGRT ---")
    descargar_archivo(URL_OXCGRT, ARCHIVO_OXCGRT, forzar)
