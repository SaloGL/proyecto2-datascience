from src.rutas import CARPETA_PROCESADOS, ARCHIVO_PARTIDOS, ARCHIVO_EQUIVALENCIAS, ARCHIVO_REPORTE
from src.descargador import descargar_todo
from src.cargador import cargar_football_data, cargar_transfermarkt, cargar_oxcgrt
from src.integrador import construir_equivalencias, integrar_fuentes
from src.estadisticas import resumen_por_periodo


def main():
    print("--- 1. DESCARGA DE DATOS (datos/raw) ---")
    descargar_todo()

    print("\n--- 2. CARGA Y LIMPIEZA ---")
    df_fd = cargar_football_data()
    df_tm = cargar_transfermarkt()
    df_ox = cargar_oxcgrt()

    if df_fd.empty or df_tm.empty or df_ox.empty:
        print("Error: no se pudieron cargar todas las fuentes. Revisa la carpeta datos/raw.")
        return

    print(f"football-data: {len(df_fd)} partidos | Transfermarkt: {len(df_tm)} partidos | OxCGRT: {len(df_ox)} días-país")

    print("\n--- 3. INTEGRACIÓN ---")
    equivalencias = construir_equivalencias(df_fd, df_tm)
    df_partidos, reporte = integrar_fuentes(df_fd, df_tm, df_ox, equivalencias)
    print(reporte.to_string(index=False))

    print("\n--- 4. GUARDADO (datos/procesados) ---")
    CARPETA_PROCESADOS.mkdir(parents=True, exist_ok=True)
    df_partidos.to_csv(ARCHIVO_PARTIDOS, index=False)
    equivalencias.to_csv(ARCHIVO_EQUIVALENCIAS, index=False)
    reporte.to_csv(ARCHIVO_REPORTE, index=False)
    print(f"Guardado: {ARCHIVO_PARTIDOS.name}, {ARCHIVO_EQUIVALENCIAS.name}, {ARCHIVO_REPORTE.name}")

    print("\n--- 5. RESUMEN POR PERIODO ---")
    print(resumen_por_periodo(df_partidos).round(2).to_string())
    print("\nListo. Ahora ejecuta: python -m streamlit run app.py")


if __name__ == "__main__":
    main()
