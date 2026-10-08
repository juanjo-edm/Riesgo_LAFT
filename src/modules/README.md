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

### 1. `filters.py` (Módulo de Filtros)

Controla la barra lateral y los parámetros de filtrado global del usuario.

- **UI (`filters_ui`):**
  - Selector de vista territorial (`vista`): `"Municipios"` o `"Departamentos"`.
  - Selector de departamento (`departamento`): `"Todos"` o un departamento específico.
  - Selector condicional de municipio (`municipio`): visible únicamente cuando `vista == "Municipios"`.
  - Grupo de casillas de verificación para las 13 dimensiones (`dimensiones`).
  - Grupo dependiente de fuentes e indicadores (`fuentes`): se actualiza dinámicamente según las dimensiones marcadas.
  - Niveles de intensidad (`niveles`): `Bajo`, `Medio`, `Alto`, `Muy alto`.
  - Botón de reinicio rápido (`clear_filters`).
- **Servidor (`filters_server`):**
  - Mantiene la reactividad entre filtros dependientes (ej. al cambiar de departamento, actualiza la lista de municipios).
  - Devuelve un objeto reactivo `state()` con el diccionario de filtros activos:
    ```python
    {
        "vista": "Municipios" | "Departamentos",
        "departamento": str,
        "municipio": str,
        "dimensiones": list[str],
        "fuentes": list[str],
        "niveles": list[str]
    }
    ```

---

### 2. `map.py` (Módulo de Mapa Interactivo con ipyleaflet)

Renderiza el mapa coroplético vectorial de Colombia con **ipyleaflet** y tarjetas métricas nativas de **bslib** (`ui.value_box`).

- **UI (`map_ui`):**
  - Fila superior de tarjetas de valor (`ui.value_box`) con iconos FontAwesome accesibles (`faicons`).
  - Tarjeta de mapa (`ui.card(..., full_screen=True, min_height="650px")`) que aloja `shinywidgets.output_widget("territory_map")`.
- **Servidor (`map_server`):**
  - **Métricas:** Calcula en tiempo real el total de territorios visibles, el puntaje promedio activo, la categoría de riesgo predominante con badge semántico y la población total cubierta.
  - **Mapa Vectorial Nativo:** Construido por sesión a través de `@render_widget` y `build_ipyleaflet_map`. Aplica coropleta con paleta accesible, control de escala, control de pantalla completa, leyenda fija (`LegendControl`) e Info Box interactivo en tiempo real (`WidgetControl`) al posicionar el cursor sobre cada territorio.
  - **Sin Iframes:** Integrado directamente en el canal WebSocket de Shiny for Python a través de `shinywidgets`, garantizando máxima velocidad y compatibilidad con Posit Cloud y Posit Connect.

---

### 3. `rankings.py` (Módulo de Rankings y Clasificaciones)

Presenta las tablas de posición ordenadas por el índice territorial activo.

- **UI (`rankings_ui`):**
  - Nota metodológica explicativa sobre la escala relativa.
  - Tarjetas de conteo con la distribución de territorios por cada uno de los 4 niveles de riesgo.
  - Botón de descarga de datos (`download_csv`).
  - Grilla de datos interactiva (`tabla_ranking`).
- **Servidor (`rankings_server`):**
  - Utiliza `render.DataGrid` de Shiny con soporte de filtros por columna, ordenamiento multicriterio y paginación.
  - Incluye un controlador `@session.download` para exportar la tabla visible directamente a CSV en formato UTF-8 con BOM (compatible con Excel).

---

### 4. `profile.py` (Módulo de Perfil Municipal)

Ficha técnica y diagnóstico individual para un municipio seleccionado.

- **UI (`profile_ui`):**
  - Resumen demográfico y tarjetas métricas (Departamento, Nivel, Índice, Ranking nacional).
  - Gráfico radial interactivo de telaraña (*radar/spider chart*).
  - Tabla de desglose de las 13 dimensiones con puntuación y valor estandarizado ($z$-score).
- **Servidor (`profile_server`):**
  - Obtiene el municipio seleccionado en los filtros globales.
  - Genera el gráfico radial con **Plotly** comparando las 13 dimensiones del municipio frente al promedio nacional.
  - Emite el HTML interactivo del gráfico mediante `fig.to_html(include_plotlyjs="cdn", full_html=False)`, garantizando máxima velocidad de renderizado sin dependencias pesadas de Jupyter.

---

### 5. `department_profile.py` (Módulo de Perfil Departamental)

Diagnóstico integral para un departamento seleccionado.

- **UI (`department_profile_ui`):**
  - Resumen métrico del departamento (Población total, número de municipios, índice ponderado y ranking nacional).
  - Gráfico radial departamental con Plotly.
  - Tabla de dimensiones con puntaje ponderado.
- **Servidor (`department_profile_server`):**
  - Calcula las intensidades departamentales como el **promedio ponderado por población municipal** de sus municipios miembros:
    $$\bar{s}_j = \frac{\sum_{i \in \text{Depto}} s_{ij} \times \text{Población}_i}{\sum_{i \in \text{Depto}} \text{Población}_i}$$
  - Renderiza el gráfico de telaraña comparando la huella del departamento frente al consolidado nacional.

---

## 🔄 Contrato de Comunicación entre Módulos

En [`app.py`](file:///Users/juanjoseecheverry/Library/Mobile%20Documents/com~apple~CloudDocs/Personal%20Code%20Portfolio/Riesgo%20LAFT/app.py), los módulos se comunican a través de **calculadores reactivos (`reactive.calc`)**:

1. `filtros = filters_server("filters", app_data)`: Genera el estado activo de filtros.
2. `active_scores()`: Evalúa si hay recálculo focalizado (dimensiones o fuentes específicas) y produce las tablas actualizadas de municipios y departamentos.
3. `filtered_data()`: Aplica los filtros de departamento seleccionado y niveles de riesgo, alimentando a `map_server` y `rankings_server`.
4. `profile_server` y `department_profile_server` consumen directamente los reactivos de datos filtrados para reflejar los cambios instantáneamente.
