import pandas as pd
import matplotlib.pyplot as plt

# Paleta fija para todo el dashboard: el local siempre azul y el visitante siempre naranja
COLOR_LOCAL = "#4C9BE8"
COLOR_VISITANTE = "#F28E2B"
COLOR_EMPATE = "#8C8C8C"
COLOR_TEXTO = "white"
COLOR_PERIODOS = {
    "Antes del COVID": "#4C9BE8",
    "Sin público": "#E15759",
    "Aforo parcial": "#EDC948",
    "Regreso del público": "#59A14F",
}


def aplicar_estilo(fig, ax) -> None:
    """
    Fondo transparente y texto blanco para que combine con el tema oscuro de Streamlit.
    """
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    ax.tick_params(colors=COLOR_TEXTO)
    ax.xaxis.label.set_color(COLOR_TEXTO)
    ax.yaxis.label.set_color(COLOR_TEXTO)
    ax.title.set_color(COLOR_TEXTO)
    for lado in ["top", "right"]:
        ax.spines[lado].set_visible(False)
    for lado in ["left", "bottom"]:
        ax.spines[lado].set_color("#666666")


def graficar_resultados_por_periodo(resumen: pd.DataFrame) -> plt.Figure:
    """
    Barras horizontales al 100 %: cómo terminan los partidos (gana local / empate / gana visitante).
    """
    if resumen.empty:
        print("Advertencia: el resumen está vacío. No se puede generar la gráfica.")
        return None

    fig, ax = plt.subplots(figsize=(12, 0.55 * len(resumen) + 0.9))
    periodos = resumen.index[::-1]  # el primer periodo arriba
    izquierda = pd.Series(0.0, index=periodos)

    for columna, etiqueta, color in [("pct_gana_local", "Gana local", COLOR_LOCAL),
                                     ("pct_empate", "Empate", COLOR_EMPATE),
                                     ("pct_gana_visitante", "Gana visitante", COLOR_VISITANTE)]:
        valores = resumen.loc[periodos, columna]
        ax.barh(periodos, valores, left=izquierda, color=color, label=etiqueta, height=0.6)
        for i, (valor, inicio) in enumerate(zip(valores, izquierda)):
            ax.text(inicio + valor / 2, i, f"{valor:.0f} %", ha="center", va="center",
                    color="black", fontweight="bold", fontsize=11)
        izquierda += valores

    ax.set_xlim(0, 100)
    ax.set_xticks([])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=3, frameon=False, labelcolor=COLOR_TEXTO)
    aplicar_estilo(fig, ax)
    ax.spines["bottom"].set_visible(False)
    plt.tight_layout()
    return fig


def graficar_ventaja_por_periodo(resumen: pd.DataFrame, columna: str, titulo: str) -> plt.Figure:
    """
    Una barra por periodo con la ventaja del local (local - visitante) en el indicador elegido.
    """
    if resumen.empty:
        print("Advertencia: el resumen está vacío. No se puede generar la gráfica.")
        return None

    fig, ax = plt.subplots(figsize=(5, 3.6))
    colores = [COLOR_PERIODOS.get(p, COLOR_EMPATE) for p in resumen.index]
    barras = ax.bar(resumen.index, resumen[columna], color=colores)
    ax.bar_label(barras, labels=[f"{v:+.2f}" for v in resumen[columna]], color=COLOR_TEXTO,
                 fontweight="bold", padding=3)
    ax.axhline(0, color="#999999", linewidth=1)

    ax.set_title(titulo, fontweight="bold", fontsize=12)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    plt.xticks(rotation=20, ha="right")
    # Margen arriba y abajo para que las etiquetas no choquen con los ejes
    rango = max(abs(resumen[columna].max()), abs(resumen[columna].min()), 0.01)
    ax.set_ylim(min(0, resumen[columna].min()) - 0.15 * rango, max(0, resumen[columna].max()) + 0.2 * rango)
    aplicar_estilo(fig, ax)
    plt.tight_layout()
    return fig


def graficar_evolucion_mensual(mensual: pd.DataFrame) -> plt.Figure:
    """
    Línea de la ventaja de puntos del local mes a mes, con la ocupación de los estadios
    como barras de fondo. Permite ver cómo cae la ventaja cuando se vacían las tribunas.
    """
    if mensual.empty:
        print("Advertencia: no hay datos mensuales. No se puede generar la gráfica.")
        return None

    fig, ax = plt.subplots(figsize=(12, 4))
    ax_fondo = ax.twinx()

    ocupacion = mensual["ocupacion"].fillna(0) * 100
    ax_fondo.bar(mensual.index, ocupacion, width=25, color="#FFFFFF", alpha=0.12)
    ax_fondo.set_ylim(0, 300)  # las barras ocupan solo el tercio inferior
    ax_fondo.set_yticks([])
    ax_fondo.patch.set_alpha(0.0)
    for lado in ["top", "right", "left", "bottom"]:
        ax_fondo.spines[lado].set_visible(False)

    tendencia = mensual["ventaja_puntos"].rolling(3, min_periods=1).mean()
    ax.plot(mensual.index, mensual["ventaja_puntos"], color=COLOR_LOCAL, alpha=0.35, marker="o", markersize=3)
    ax.plot(mensual.index, tendencia, color=COLOR_LOCAL, linewidth=3, label="Ventaja de puntos (promedio 3 meses)")
    ax.axhline(0, color="#999999", linewidth=1)

    sin_publico = mensual.index[ocupacion < 5]
    if len(sin_publico) > 0:
        ax.axvspan(sin_publico.min(), sin_publico.max(), color=COLOR_PERIODOS["Sin público"], alpha=0.15)
        ax.text(sin_publico.min(), ax.get_ylim()[1] * 0.92, "  Estadios vacíos", color=COLOR_PERIODOS["Sin público"],
                fontweight="bold")

    ax.set_ylabel("Puntos local − puntos visitante")
    ax.legend(loc="upper right", frameon=False, labelcolor=COLOR_TEXTO)
    aplicar_estilo(fig, ax)
    ax.set_zorder(ax_fondo.get_zorder() + 1)
    ax.patch.set_visible(False)
    plt.tight_layout()
    return fig
