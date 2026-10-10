# Paquete de la Aplicación (`src/`)

Este directorio contiene el código fuente de soporte, algoritmos estadísticos, servicios de datos y componentes visuales para la aplicación del **Atlas Territorial de Problemáticas en Colombia (Shiny for Python)**.

---

## 📁 Estructura del Paquete

```text
src/
├── __init__.py
├── config.py                 # Constantes, paletas de colores y dimensiones oficiales
├── critic.py                 # Algoritmo de ponderación objetiva CRITIC
├── calculator.py             # Motor de cálculo reactivo, K-Means dinámico y agregación
├── data_loader.py            # Servicio de carga en memoria con soporte Parquet / GeoParquet
├── prepare_data.py           # Pipeline ETL para procesar Excel a Parquet y GeoJSON
├── components/               # Componentes de UI reutilizables
│   ├── __init__.py
│   └── cards.py              # Tarjetas de resumen métrico, badges de riesgo y notas
├── visualizations/           # Constructores de gráficos y mapas
│   ├── __init__.py
│   ├── map_builder.py        # Generador de mapas coropléticos interactivos con ipyleaflet
│   └── radar.py              # Generador de gráficos radiales interactivos con Plotly
├── modules/                  # Módulos Shiny independientes (UI + Server)
│   ├── ...
│   └── README.md             # Documentación detallada de módulos
└── README.md                 # Este archivo
```

---

## ⚙️ Descripción de Componentes Clave

### 1. `config.py`
Define la configuración central del proyecto:
- `DIMENSIONES_TERRITORIALES`: Lista de los 13 identificadores oficiales (`CONT`, `CORR`, `AMBI`, `EXTC`, `MIEX`, `NARC`, `TFT`, `TRAT`, `HURTO`, `HOMICIDIOS`, `VIOLENCIA_SEXUAL`, `ARMAS`, `CAPTURAS`).
- `DIMENSION_LABELS`: Diccionario con los nombres completos en español de cada dimensión.
- `INTENSIDAD_LEVELS`: Categorías de riesgo (`Bajo`, `Medio`, `Alto`, `Muy alto`).
- `INTENSIDAD_PALETTE`: Paleta de colores oficial accesible (Okabe-Ito / semáforo territorial).

### 2. `critic.py`
Implementa las funciones estadísticas requeridas por la metodología CRITIC (*Criteria Importance Through Intercriteria Correlation*):
- `winsorize_series(series, probs=(0.01, 0.99))`: Recorte de valores extremos para mitigar sesgos por casos atípicos.
- `minmax_scale(series)`: Normalización lineal al intervalo $[0, 1]$.
- `calculate_critic_weights(df, method="pearson")`: Cuantifica la desviación estándar (contraste) y penaliza la correlación entre criterios para producir ponderaciones objetivas que suman $1.0$.

### 3. `calculator.py`
Lógica reactiva para el recálculo dinámico de índices territoriales:
- `score_values_to_level(values)`: Ejecuta un clustering **K-Means ($k=4$)** con semilla `random_state=123` y mapea los clusters a niveles de riesgo ordenados según la magnitud de sus centroides.
- `build_municipal_active(...)`: Calcula el índice activo de cada municipio según las dimensiones o fuentes seleccionadas.
- `build_department_active(...)`: Agrega los puntajes municipales a nivel departamental utilizando un promedio ponderado por población censal.
- `score_to_risk_shared(...)`: Asegura una escala uniforme y comparable cuando se recalcula el riesgo.

### 4. `data_loader.py`
Servicio de acceso a datos de alto rendimiento:
- Lee los archivos `.parquet` de `Data/processed/` en microsegundos gracias a PyArrow.
- Carga las geometrías simplificadas desde `Data/geodata/mapa_municipios.parquet` y `mapa_departamentos.parquet`, logrando una inicialización prácticamente instantánea en comparación con archivos GeoJSON o RDS pesados.
- Implementa un patrón de caché singleton en memoria para evitar lecturas de disco innecesarias durante la sesión de usuario.

### 5. `prepare_data.py` (ETL)
Script que transforma el libro público consolidado `Output/atlas_territorial_publico.xlsx` en tablas tipadas Parquet:
- Formatea con exactitud los códigos Divipola a 5 dígitos para municipios y 2 dígitos para departamentos.
- Valida tipos de datos (enteros, flotantes, booleanos).
- Genera la tabla larga `dimensiones_municipales.parquet` requerida por las fichas técnicas.

---

## 🎨 Componentes Visuales y Sistema de Diseño

- **`src/components/cards.py`:**
  - `kpi_card(title, value, subtitle, unit, indicator_color)`: Tarjeta KPI neutral de alta jerarquía con números tabulares y contexto censal DANE 2018.
  - `risk_badge(level, count)`: Pastilla semántica con dot indicador y contraste WCAG 2.2 AA según el nivel de riesgo (`Bajo`, `Medio`, `Alto`, `Muy alto`).
  - `scenario_badge(recalculated, label, active_count)`: Indicador contextual reactivo que diferencia el Índice Territorial General de un escenario recalculado por CRITIC.
  - `metric_card(title, value, subtitle, border_color)`: Tarjeta de resumen métrico con acento para fichas de diagnóstico territorial.
  - `empty_state(message, instruction)`: Mensaje visual instructivo y accesible ante ausencia de selección.
  - `method_note(text, title)`: Caja de notas metodológicas y advertencias analíticas con borde interactivo.
- **`src/visualizations/map_builder.py`:**
  - `build_ipyleaflet_map(...)`: Inicializa el explorador cartográfico `ipyleaflet.Map` con capa base neutra `Esri.WorldGrayCanvas`, controles (`ScaleControl`, `FullScreenControl`, `LegendControl`) y callbacks de hover/clic con control de generación (`_atlas_generation`) para descartar eventos en tránsito.
  - `update_ipyleaflet_map(...)`: Actualiza in-situ los datos y estilos de la capa `GeoJSON` sin recrear el widget, preservando el viewport manual cuando solo cambian puntajes.
  - `prepare_geojson_data(...)`: Cruza geometrías y datos, preserva sin simplificar el polígono seleccionado, aplica sombreado exclusivo al territorio enfocado (`fillOpacity: 0.88`, borde `#315EEA`) y deja los vecinos con relleno transparente para mantener el contexto geográfico.
  - `padded_bounds(...)`, `viewport_for_bounds(...)`, `frame_map(...)`, `viewport_has_arrived(...)`: Motor de encuadre Web Mercator con margen del 10% por lado y confirmación del viewport real en el cliente.
  - `format_feature_info_html(...)` y `format_initial_info_box()`: Generadores HTML para el Info Box flotante (modo inspección por cursor y modo `📍 Selección fijada`).
- **`src/visualizations/radar.py`:**
  - `create_radar_chart(...)`: Construye el gráfico radial (*spider chart*) interactivo en Plotly comparando las 13 dimensiones del territorio frente a la media nacional.
  - `create_dimensions_bar_chart(...)`: Construye el gráfico de barras horizontales ordenadas para comparar de manera directa la vulnerabilidad por dimensión frente al referente nacional.
  - `empty_radar_figure(...)`: Estado visual elegante cuando no hay territorio activo.
