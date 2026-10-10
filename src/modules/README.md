# Módulos de la Aplicación Shiny (`src/modules/`)

Este directorio contiene los módulos independientes de interfaz y servidor de la aplicación **Shiny for Python (`shiny`)**. Cada módulo encapsula su propio espacio de nombres (*namespace*), lógica reactiva y componentes visuales, siguiendo el patrón oficial `@module.ui` y `@module.server`.

---

## 📁 Arquitectura de Módulos

```text
src/modules/
├── __init__.py
├── filters.py             # Módulo de barra lateral (Sidebar) y controles reactivos
├── map.py                 # Módulo de visualización cartográfica interactiva con ipyleaflet
├── rankings.py            # Módulo de tabla clasificatoria (DataGrid) y exportación
├── profile.py             # Ficha técnica municipal y gráfico de telaraña Plotly
├── department_profile.py  # Ficha departamental con agregación ponderada y radar
└── README.md              # Este archivo de documentación
```

---

## 🧩 Detalle de Módulos

### 1. `filters.py` (Módulo de Filtros y Búsqueda Predictiva)

Controla la barra lateral, la búsqueda predictiva de territorios y los parámetros de filtrado global del usuario.

- **UI (`filters_ui`):**
  - Indicador reactivo del escenario activo (`scenario_status`).
  - Selector de vista territorial (`vista`): `"Municipios"` o `"Departamentos"`.
  - Selector predictivo de departamento (`departamento`, vía `ui.input_selectize` con búsqueda instantánea).
  - Selector condicional predictivo de municipio (`municipio`, vía `ui.input_selectize`), visible cuando `vista == "Municipios"`.
  - Acordeón de las 13 dimensiones (`dimensiones`) y subgrupo dependiente de fuentes e indicadores (`fuentes`).
  - Acordeón de niveles de intensidad (`niveles`): `Bajo`, `Medio`, `Alto`, `Muy alto`.
  - Botón de reinicio rápido (`clear_filters`).
- **Servidor (`filters_server`):**
  - Mantiene la reactividad entre filtros dependientes y detecta selecciones explícitas del usuario (`territory_selection`) para activar el enfoque cartográfico automático (por ejemplo, al elegir un departamento específico cambia automáticamente a vista `"Departamentos"` y lo encuadra).
  - Devuelve una tupla `(state, map_focus, map_revision, select_from_map)`:
    - `state()`: cálculo reactivo con el diccionario de filtros activos (`vista`, `departamento`, `municipio`, `dimensiones`, `fuentes`, `niveles`).
    - `map_focus`: valor reactivo con el territorio enfocado (`{"nivel": ..., "codigo": ...}` o `None`).
    - `map_revision`: contador reactivo de revisiones de selección para re-encuadrar incluso al re-seleccionar el mismo territorio.
    - `select_from_map(code, props)`: callback para sincronizar los selectores laterales cuando el usuario hace clic sobre un polígono en el mapa.

---

### 2. `map.py` (Módulo de Mapa Interactivo con ipyleaflet)

Renderiza el explorador coroplético vectorial de Colombia con **ipyleaflet**, tarjetas KPI neutrales (`kpi_card`), Info Box flotante reactiva y ficha contextual inferior.

- **UI (`map_ui`):**
  - Fila superior de tarjetas KPI con tipografía destacada, números tabulares y referencia al Censo DANE 2018.
  - Tarjeta de mapa (`ui.card(..., full_screen=True)`) con alerta condicional de geometría (`focus_notice`), contenedor `output_widget("territory_map")` sobre lienzo `Esri.WorldGrayCanvas` e Info Box flotante superpuesta (`ui.output_ui("floating_info_box")`).
  - Drawer contextual (`selected_territory_drawer`) que presenta el territorio seleccionado con DIVIPOLA, índice activo, badge semántico, población y posición en el ranking activo.
- **Servidor (`map_server`):**
  - **Métricas (`metrics_summary`):** Calcula en tiempo real el total de territorios visibles, el puntaje promedio activo, la categoría de riesgo predominante y la población total cubierta.
  - **Actualización In-Situ y Encuadre (`_update_map` y `_frame_map`):** Reutiliza la instancia `ipyleaflet.Map` actualizando únicamente los datos y estilos de su capa `GeoJSON` (`update_ipyleaflet_map`) y aplicando el encuadre Web Mercator con margen del 10% (`frame_map`) una vez que el cliente confirma `pixel_bounds`.
  - **Info Box y Selección:** Muestra el detalle en tiempo real al pasar el cursor (`hovered_territory`) o mantiene fija la tarjeta del territorio seleccionado (`📍 Selección fijada`).

---

### 3. `rankings.py` (Módulo de Rankings y Clasificaciones)

Presenta las tablas de posición ordenadas por el índice territorial activo.

- **UI (`rankings_ui`):**
  - Nota metodológica explicativa sobre la escala relativa y la clasificación K-Means.
  - Tarjetas de conteo con la distribución de territorios por cada uno de los 4 niveles de riesgo.
  - Botón de descarga de datos (`download_csv`).
  - Grilla de datos interactiva (`tabla_ranking`).
- **Servidor (`rankings_server`):**
  - Utiliza `render.DataGrid` de Shiny con soporte de filtros por columna, ordenamiento multicriterio y paginación.
  - Incluye un controlador `@session.download` para exportar la tabla visible directamente a CSV en formato UTF-8 con BOM (compatible con Excel), preservando códigos DIVIPOLA.

---

### 4. `profile.py` (Módulo de Perfil Municipal)

Ficha técnica y diagnóstico individual para un municipio seleccionado estructurada en 5 partes.

- **UI (`profile_ui`):**
  - Resumen demográfico y tarjetas métricas (Departamento, Nivel de Riesgo, Índice Territorial y Ranking nacional).
  - Pestañas con selector de visualización: **Gráfico Radial (Spider Chart)** y **Barras Comparativas** frente al promedio nacional.
  - Callout de dimensiones de mayor incidencia territorial.
  - Tabla de desglose de las 13 dimensiones con puntuación municipal, promedio nacional y valor estandarizado ($z$-score).
- **Servidor (`profile_server`):**
  - Obtiene el municipio seleccionado en los filtros globales.
  - Genera el gráfico radial y el gráfico de barras horizontales con **Plotly** vía `@render_plotly`.
  - Renderiza el desglose multidimensional tabular con `render.DataGrid`.

---

### 5. `department_profile.py` (Módulo de Perfil Departamental)

Diagnóstico integral para un departamento seleccionado.

- **UI (`department_profile_ui`):**
  - Resumen métrico del departamento (Población total, número de municipios, índice ponderado y ranking nacional).
  - Pestañas con alternancia entre **Gráfico Radial Departamental** y **Barras Comparativas**.
  - Callout de dimensiones destacadas del departamento.
  - Tabla de dimensiones con puntaje departamental ponderado y referencia nacional.
- **Servidor (`department_profile_server`):**
  - Calcula las intensidades departamentales como el **promedio ponderado por población municipal** de sus municipios miembros:
    $$\bar{s}_j = \frac{\sum_{i \in \text{Depto}} s_{ij} \times \text{Población}_i}{\sum_{i \in \text{Depto}} \text{Población}_i}$$
  - Renderiza los gráficos interactivos de telaraña y barras comparativas en Plotly comparando la huella del departamento frente al consolidado nacional.

---

## 🔄 Contrato de Comunicación entre Módulos

En [`app.py`](file:///Users/juanjoseecheverry/Library/Mobile%20Documents/com~apple~CloudDocs/Personal%20Code%20Portfolio/Riesgo%20LAFT/app.py), los módulos se comunican a través de **calculadores y valores reactivos (`reactive.calc`, `reactive.Value`)**:

1. `filtros, map_focus, map_revision, select_from_map = filters_server("filters", app_data)`: Genera el estado activo de filtros y coordina el enfoque bidireccional entre los selectores y el mapa.
2. `active_scores()`: Evalúa si hay recálculo focalizado (dimensiones o fuentes específicas) y produce las tablas actualizadas de municipios y departamentos.
3. `filtered_data()`: Aplica los filtros de departamento seleccionado y niveles de riesgo, alimentando a `map_server` y `rankings_server`.
4. `selected_territory()`: Resuelve el registro completo del municipio o departamento actualmente enfocado en `map_focus()`, limpiando automáticamente la selección si queda excluida por un filtro posterior.
5. `profile_server` y `department_profile_server` consumen directamente los reactivos de datos filtrados para reflejar los cambios instantáneamente.
