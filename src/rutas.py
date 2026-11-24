from pathlib import Path

# Rutas relativas a la carpeta del proyecto.
# Así el código funciona en cualquier computador, sin rutas fijas como C:\Users\...
CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_DATOS = CARPETA_PROYECTO / "datos"
CARPETA_RAW = CARPETA_DATOS / "raw"
CARPETA_PROCESADOS = CARPETA_DATOS / "procesados"

CARPETA_FOOTBALL_DATA = CARPETA_RAW / "football_data"
ARCHIVO_TRANSFERMARKT = CARPETA_RAW / "transfermarkt_games.csv.gz"
ARCHIVO_OXCGRT = CARPETA_RAW / "oxcgrt_compact_national_v1.csv"

ARCHIVO_PARTIDOS = CARPETA_PROCESADOS / "partidos_integrados.csv"
ARCHIVO_EQUIVALENCIAS = CARPETA_PROCESADOS / "equivalencias_equipos.csv"
ARCHIVO_REPORTE = CARPETA_PROCESADOS / "reporte_integracion.csv"

# Ligas analizadas: nombre en el dashboard -> (carpeta en el espejo de football-data,
# código de competición en Transfermarkt, país en OxCGRT)
LIGAS = {
    "Premier League": ("premier-league", "GB1", "GBR"),
    "LaLiga": ("la-liga", "ES1", "ESP"),
    "Bundesliga": ("bundesliga", "L1", "DEU"),
    "Serie A": ("serie-a", "IT1", "ITA"),
    "Ligue 1": ("ligue-1", "FR1", "FRA"),
}

# Temporadas 2017-18 a 2023-24 (código de football-data: "1718" = 2017-18)
TEMPORADAS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324"]
