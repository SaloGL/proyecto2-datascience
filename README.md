# ¿Cuánto de la ventaja de jugar en casa se debe al público?

Proyecto 2 · Aplicaciones en Ciencia de Datos (DATA-1002) · Universidad de los Andes

Dashboard que compara el rendimiento del equipo local y las decisiones arbitrales **antes, durante y después
de los partidos sin público por el COVID** en las cinco grandes ligas europeas (2017-18 a 2023-24).

## Cómo ejecutarlo (en cualquier computador)

Requisitos: Python 3.10 o superior. Todos los comandos se ejecutan **dentro de la carpeta `ventaja_local`**.

> **Importante en Windows:** descomprime el .zip en una ruta corta, por ejemplo `C:\proyectos\ventaja_local`.
> Windows limita las rutas a 260 caracteres; si la carpeta está muy anidada (Documentos\Universidad\Semestre\...),
> la instalación de Streamlit queda incompleta y aparece el error `No module named 'streamlit.proto'`.
> Si ya te pasó: mueve la carpeta a una ruta corta, borra la carpeta `.venv` y repite los pasos.

```powershell
cd ventaja_local
```

1. Crear un entorno virtual (evita conflictos con otras librerías instaladas):

```powershell
python -m venv .venv
```

```powershell
.venv\Scripts\activate
```

En Mac o Linux: `source .venv/bin/activate`

2. Instalar las librerías:

```powershell
python -m pip install -r requirements.txt
```

3. (Opcional) Volver a generar los datos procesados. Descarga lo que falte en `datos/raw`, limpia, integra
   y guarda el resultado en `datos/procesados`. Los datos ya vienen incluidos, así que este paso no es obligatorio:

```powershell
python main.py
```

4. Abrir el dashboard:

```powershell
python -m streamlit run app.py
```

> Se usa `python -m streamlit` en lugar de `streamlit` para asegurar que se ejecute el Streamlit del entorno virtual.
> El código no usa rutas fijas: todas las rutas se calculan a partir de la carpeta del proyecto (`src/rutas.py`).

## Estructura

```
ventaja_local/
├── app.py                  # Dashboard en Streamlit
├── main.py                 # Pipeline: descarga -> limpieza -> integración -> guardado
├── requirements.txt
├── .streamlit/config.toml  # Tema claro (blanco) del dashboard
├── datos/
│   ├── raw/                # Datos tal como se descargaron (sin modificar)
│   │   ├── football_data/  # 35 CSV: 5 ligas x 7 temporadas
│   │   ├── transfermarkt_games.csv.gz
│   │   └── oxcgrt_compact_national_v1.csv
│   └── procesados/         # Resultado de main.py
│       ├── partidos_integrados.csv   # Tabla final: 1 fila por partido (alimenta el dashboard)
│       ├── equivalencias_equipos.csv # Nombres football-data -> Transfermarkt
│       └── reporte_integracion.csv   # Cardinalidad, registros sin pareja y duplicados
└── src/
    ├── rutas.py            # Rutas relativas, ligas y temporadas
    ├── descargador.py      # Descarga de las tres fuentes
    ├── cargador.py         # Carga y limpieza de cada fuente
    ├── integrador.py       # Unión de fuentes y clasificación por periodo
    ├── estadisticas.py     # Filtros, indicadores y hallazgos
    └── visualizador.py     # Gráficas (matplotlib)
```

## Fuentes

| # | Fuente | Qué aporta | Unidad | Cobertura | Licencia |
|---|---|---|---|---|---|
| 1 | [football-data.co.uk](https://www.football-data.co.uk), vía el espejo [datasets/football-datasets](https://github.com/datasets/football-datasets) | Resultado, tiros, tiros a puerta, faltas, tarjetas | Partido | 2017-18 a 2023-24 | PDDL 1.0 |
| 2 | [Transfermarkt – player-scores (Kaggle, davidcariboo)](https://www.kaggle.com/datasets/davidcariboo/player-scores), archivo `games.csv` | Asistencia, estadio, árbitro | Partido | 2017-18 a 2023-24 | CC0 |
| 3 | [Oxford COVID-19 Government Response Tracker](https://github.com/OxCGRT/covid-policy-dataset) | Restricciones a eventos públicos (C3M), reuniones (C4M), índice de rigurosidad | País-día | 2020-01-01 a 2022-12-31 | CC BY 4.0 |

La página original de football-data.co.uk está bloqueada en algunas redes de Colombia (es un sitio de apuestas),
por eso se descarga desde su espejo público en GitHub, que contiene los mismos archivos.

## Integración

1. **football-data + Transfermarkt** por `liga + fecha + equipo local + equipo visitante`.
   Los nombres de los equipos se escriben distinto en cada fuente (`Man City` vs `Manchester City Football Club`).
   La tabla de equivalencias se construye cruzando partidos de la misma liga, el mismo día y con el mismo marcador,
   y tomando el nombre que más veces coincide. Resultado: 145 equipos emparejados, 12.601 de 12.607 partidos unidos
   con cardinalidad 1 a 1, 0 duplicados.
2. **+ OxCGRT** por `país de la liga + fecha`. Muchos partidos a 1 día-país.

### Periodos

| Periodo | Regla |
|---|---|
| Antes del COVID | Partidos antes del 8 de marzo de 2020 |
| Sin público | Entre marzo de 2020 y junio de 2022, sin asistencia registrada y con restricciones a eventos públicos (OxCGRT ≥ 1) |
| Aforo parcial | En ese mismo lapso, asistencia menor al 75 % de la asistencia habitual del estadio |
| Regreso del público | Asistencia de nuevo en niveles normales, o partidos desde julio de 2022 |

## Limitaciones

- No es un experimento perfecto: en el mismo periodo hubo cinco cambios por partido, calendario comprimido y VAR introducido en años distintos.
- Transfermarkt no registra asistencia 0: la ausencia de dato se interpreta como “sin público” solo cuando OxCGRT indica restricciones.
- football-data solo trae el árbitro de la Premier League; para las demás ligas se usa el de Transfermarkt.
- 6 partidos de football-data no encontraron pareja en Transfermarkt (se conservan sin asistencia); 5 partidos sin asistencia y sin restricciones se excluyen.
