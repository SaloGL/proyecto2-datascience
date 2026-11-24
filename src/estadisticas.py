import pandas as pd

from src.integrador import ORDEN_PERIODOS


def filtrar_partidos(df: pd.DataFrame, ligas: list, temporadas: list, periodos: list,
                     equipo: str = "Todos", condicion: str = "Local o visitante",
                     arbitro: str = "Todos") -> pd.DataFrame:
    """
    Aplica los filtros del dashboard y retorna los partidos que cumplen todos.
    """
    if df.empty:
        return df

    mascara = (
        df["liga"].isin(ligas)
        & df["temporada"].isin(temporadas)
        & df["periodo"].isin(periodos)
    )

    if equipo != "Todos":
        if condicion == "Solo como local":
            mascara &= df["local"] == equipo
        elif condicion == "Solo como visitante":
            mascara &= df["visitante"] == equipo
        else:
            mascara &= (df["local"] == equipo) | (df["visitante"] == equipo)

    if arbitro != "Todos":
        mascara &= df["arbitro"] == arbitro

    return df[mascara]


def resumen_por_periodo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula los indicadores principales por periodo, siempre desde el punto de vista del local.
    """
    if df.empty:
        return pd.DataFrame()

    resumen = df.groupby("periodo").agg(
        partidos=("resultado", "size"),
        pct_gana_local=("resultado", lambda s: (s == "Gana local").mean() * 100),
        pct_empate=("resultado", lambda s: (s == "Empate").mean() * 100),
        pct_gana_visitante=("resultado", lambda s: (s == "Gana visitante").mean() * 100),
        puntos_local=("puntos_local", "mean"),
        puntos_visitante=("puntos_visitante", "mean"),
        goles_local=("goles_local", "mean"),
        goles_visitante=("goles_visitante", "mean"),
        tiros_local=("tiros_local", "mean"),
        tiros_visitante=("tiros_visitante", "mean"),
        tiros_puerta_local=("tiros_puerta_local", "mean"),
        tiros_puerta_visitante=("tiros_puerta_visitante", "mean"),
        faltas_local=("faltas_local", "mean"),
        faltas_visitante=("faltas_visitante", "mean"),
        amarillas_local=("amarillas_local", "mean"),
        amarillas_visitante=("amarillas_visitante", "mean"),
        rojas_local=("rojas_local", "mean"),
        rojas_visitante=("rojas_visitante", "mean"),
        asistencia_media=("asistencia", "mean"),
    )

    # Ventajas del local (positivo = el local está mejor que el visitante)
    resumen["ventaja_puntos"] = resumen["puntos_local"] - resumen["puntos_visitante"]
    resumen["ventaja_goles"] = resumen["goles_local"] - resumen["goles_visitante"]
    resumen["ventaja_tiros"] = resumen["tiros_local"] - resumen["tiros_visitante"]
    resumen["ventaja_tiros_puerta"] = resumen["tiros_puerta_local"] - resumen["tiros_puerta_visitante"]
    # Sesgo arbitral (positivo = el visitante recibe más que el local)
    resumen["sesgo_faltas"] = resumen["faltas_visitante"] - resumen["faltas_local"]
    resumen["sesgo_amarillas"] = resumen["amarillas_visitante"] - resumen["amarillas_local"]
    resumen["sesgo_rojas"] = resumen["rojas_visitante"] - resumen["rojas_local"]

    # Orden fijo de los periodos para que las gráficas se lean de izquierda a derecha
    orden = [p for p in ORDEN_PERIODOS if p in resumen.index]
    return resumen.loc[orden]


def serie_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula, mes a mes, la ventaja de puntos del local y la ocupación relativa media.
    """
    if df.empty:
        return pd.DataFrame()

    mensual = df.assign(mes=df["fecha"].dt.to_period("M").dt.to_timestamp()).groupby("mes").agg(
        partidos=("resultado", "size"),
        ventaja_puntos=("puntos_local", "mean"),
        puntos_visitante=("puntos_visitante", "mean"),
        ocupacion=("ocupacion_relativa", "mean"),
    )
    mensual["ventaja_puntos"] = mensual["ventaja_puntos"] - mensual["puntos_visitante"]
    return mensual[mensual["partidos"] >= 10]  # se omiten meses con muy pocos partidos


def generar_hallazgos(resumen: pd.DataFrame) -> list:
    """
    Redacta los hallazgos principales comparando 'Antes del COVID' con 'Sin público'.
    """
    hallazgos = []
    if "Antes del COVID" not in resumen.index or "Sin público" not in resumen.index:
        return ["Selecciona datos que incluyan los periodos 'Antes del COVID' y 'Sin público' para comparar."]

    antes = resumen.loc["Antes del COVID"]
    sin = resumen.loc["Sin público"]

    hallazgos.append(
        f"**Victorias del local:** {antes['pct_gana_local']:.1f} % con público vs "
        f"{sin['pct_gana_local']:.1f} % sin público ({sin['pct_gana_local'] - antes['pct_gana_local']:+.1f} puntos porcentuales)."
    )

    if antes["ventaja_puntos"] != 0:
        perdida = (1 - sin["ventaja_puntos"] / antes["ventaja_puntos"]) * 100
        hallazgos.append(
            f"**Ventaja en puntos por partido:** pasó de {antes['ventaja_puntos']:+.2f} a "
            f"{sin['ventaja_puntos']:+.2f}. Sin público se perdió cerca del {perdida:.0f} % de la ventaja de local."
        )

    hallazgos.append(
        f"**Arbitraje:** con público el visitante recibía {antes['sesgo_amarillas']:+.2f} amarillas más por partido "
        f"que el local; sin público la diferencia fue de {sin['sesgo_amarillas']:+.2f}."
    )

    if "Regreso del público" in resumen.index:
        regreso = resumen.loc["Regreso del público"]
        hallazgos.append(
            f"**Con el regreso del público** la ventaja en puntos volvió a {regreso['ventaja_puntos']:+.2f} "
            f"y el local ganó el {regreso['pct_gana_local']:.1f} % de los partidos."
        )
    return hallazgos
