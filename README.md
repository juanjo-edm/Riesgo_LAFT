# Atlas Territorial de Problemáticas en Colombia (Medición de Riesgo LAFT)

Este repositorio consolida fuentes públicas territoriales para explorar, comparar y visualizar problemáticas municipales y departamentales en Colombia y su asociación al riesgo de **Lavado de Activos y Financiación del Terrorismo (LA/FT)**.

El flujo procesa datos abiertos oficiales (vía API SoQL y bases institucionales), calcula tasas por 100.000 habitantes estandarizadas con z-scores, aplica winsorización robusta (1%–99%), estima pesos objetivos mediante **CRITIC** (*Criteria Importance Through Intercriteria Correlation*), clasifica municipios y departamentos con **K-Means ($k=4$)** y publica una aplicación interactiva en **Shiny for Python (`shiny`)** con mapas vectoriales reactivos en **ipyleaflet**, componentes modernos **bslib** (`value_box`, tarjetas adaptables) y gráficos interactivos en **Plotly**.

---

## 🏛️ Estructura del Proyecto

Siguiendo las mejores prácticas de desarrollo en Python:

```text
├── app.py                      # Entrada principal de la aplicación Shiny for Python
├── _brand.yml                  # Tokens de identidad visual y configuración de tema
├── manifest.json               # Manifiesto de despliegue para Posit Connect / Posit Cloud
├── pyproject.toml              # Definición de dependencias y configuración de uv (PEP 621)
├── requirements.txt            # Dependencias fijadas para despliegue universal
├── .here                       # Marcador de raíz del proyecto para rutas portables (pyprojroot)
├── www/                        # Recursos estáticos servidos por Shiny
│   ├── metodologia.html        # Copia pública del cuaderno metodológico compilado
│   └── styles/                 # Hojas de estilo CSS modulares (tokens, base, layout, map, etc.)
├── src/                        # Código fuente modular de la aplicación ([Ver Documentación](src/README.md))
│   ├── config.py               # Constantes, paletas y definiciones de dimensiones
│   ├── data_loader.py          # Carga y caché de datos Parquet y geometrías
│   ├── calculator.py           # Recálculo reactivo de scores y K-Means dinámico
│   ├── critic.py               # Algoritmo de ponderación objetiva CRITIC en Python
│   ├── prepare_data.py         # Pipeline ETL de conversión Excel -> Parquet/Geodata
│   ├── components/             # Componentes reutilizables de UI (cards, badges)
│   ├── modules/                # Módulos Shiny ([Ver Documentación](src/modules/README.md))
│   └── visualizations/         # Constructores de mapas ipyleaflet y gráficos Plotly
├── tests/                      # Suite de pruebas automatizadas con pytest
│   ├── test_analytical_baseline.py # Regresión estadística CRITIC, K-Means y agregación
│   ├── test_app_structure.py   # Integridad de módulos UI/Server y sistema de diseño
│   └── test_map_focus.py       # Pruebas de encuadre Web Mercator, estilos y sincronización
├── Scripts/                    # Automatización E2E y scripts de procesamiento
│   └── verify_app_ui.py        # Verificación visual y funcional multiplataforma (Playwright)
├── notebook_methodology/       # Cuaderno metodológico en Quarto ([Ver Documentación](notebook_methodology/README.md))
│   ├── data/                   # Insumos primarios del cuaderno
│   ├── images/                 # Gráficos y esquemas
│   ├── metodologia.qmd         # Cuaderno Quarto con motor Python (Jupyter + API SoQL)
│   ├── metodologia.html        # Cuaderno compilado interactivo auto-contenido
│   └── _quarto.yml             # Configuración del documento Quarto
├── Data/
│   ├── raw/                    # Libros Excel y fuentes originales
│   ├── processed/              # Tablas de alta velocidad en formato Parquet
│   └── geodata/                # Capas geoespaciales simplificadas (GeoParquet / GeoJSON)
└── Output/                     # Consolidado tabular (atlas_territorial_publico.xlsx)
```

---

## ⚙️ Requisitos e Instalación

El proyecto se gestiona con **`uv`**, el gestor de entornos ultrarrápido para Python:

```bash
# 1. Clonar el repositorio y sincronizar el entorno
uv sync
```

---

## 🚀 Cómo Ejecutar la Aplicación Web (Shiny for Python)

Desde la raíz del proyecto:

```bash
# Ejecutar la aplicación con recarga en caliente
uv run shiny run app.py --reload
```

La app estará disponible en `http://127.0.0.1:8000`.

### Funcionalidades y Sistema de Diseño (Geospatial Intelligence UI/UX):
- **🎨 Sistema de Diseño y Tokens (`_brand.yml` & `www/styles/`):** Paleta profesional en tonos azul profundo institucional (`#14243A`), azul interactivo (`#315EEA`), fondo neutro (`#F5F7FB`), tipografía Inter / Plus Jakarta Sans y tokens centralizados en CSS. Escala semántica de riesgo accesible (WCAG 2.2 AA).
- **🧭 Encabezado Compacto y Modal Metodológico:** Barra superior optimizada que maximiza el área de trabajo cartográfico, incorpora indicadores en tiempo real del motor activo y modal directo con resumen del pipeline y acceso al informe completo Quarto HTML.
- **🗺️ Explorador Cartográfico con Enfoque Inteligente:** Mapa coroplético en **ipyleaflet** sobre lienzo base neutro (`Esri World Gray Canvas`) con actualización in-situ de capas (`update_ipyleaflet_map`). Al seleccionar un municipio o departamento (por buscador o clic en el mapa), encuadra automáticamente el territorio en proyección Web Mercator con margen del 10%, resalta exclusivamente el polígono activo (`fillOpacity: 0.88`, borde `#315EEA`) y mantiene los vecinos con relleno transparente para conservar el contexto geográfico y consultarlos con el cursor. Incluye Info Box flotante reactiva, aviso ante geometrías faltantes y drawer territorial inferior.
- **📊 Tarjetas KPI Neutrales:** Indicadores clave de desempeño estructurados sobre superficies limpias, con tipografía protagonista en cifras tabulares, subtítulos contextuales y referencia explícita al Censo DANE 2018.
- **⚙️ Panel de Filtros y Búsqueda Predictiva:** Selectores `selectize` con búsqueda instantánea por texto en Departamento y Municipio, sincronizados bidireccionalmente con el mapa. Incluye acordeones colapsables para dimensiones CRITIC, indicadores específicos dependientes, niveles de intensidad y tarjeta reactiva de escenario (*Índice Global Consolidado* vs *Recálculo Personalizado CRITIC*).
- **📋 Rankings Jerárquicos y Exportación:** DataGrid interactivo con ordenamiento multicriterio, paginación, filtros por columna, badges semánticos discretos, códigos DIVIPOLA preservados con ceros a la izquierda y descarga a CSV (UTF-8 con BOM para Excel).
- **🏛️ Perfiles Territorial y Departamental:** Fichas técnicas completas organizadas en 5 secciones de diagnóstico, con selector de vista comparativa entre **gráfico radial (spider chart)** y **gráfico de barras horizontales ordenadas** frente al promedio nacional, además de desglose tabular de dimensiones estandarizadas.

---

## 🧪 Validación y Pruebas Automatizadas

El proyecto incluye suites de pruebas unitarias y de extremo a extremo (E2E) para garantizar la integridad estadística, el encuadre cartográfico y la estabilidad de la interfaz:

```bash
# 1. Ejecutar pruebas unitarias de regresión estadística, UI y enfoque cartográfico (100% pass)
uv run pytest

# 2. Ejecutar verificación visual e interacción multiplataforma con Playwright
uv run python Scripts/verify_app_ui.py
```

- **`tests/test_analytical_baseline.py`:** Verifica ponderaciones CRITIC, clustering K-Means ($k=4$) y agregación departamental ponderada por población.
- **`tests/test_app_structure.py`:** Valida la arquitectura modular UI/Server, activos estáticos y hojas de estilo CSS.
- **`tests/test_map_focus.py`:** Verifica el sombreado exclusivo del territorio seleccionado, cálculo de límites con margen del 10%, encuadre Web Mercator adaptable a escritorio/móvil y sincronización de eventos en `ipyleaflet`.
- **`Scripts/verify_app_ui.py`:** Ejecuta pruebas E2E en navegador real (1440×900 escritorio y 390×844 móvil) y genera capturas de verificación en `Output/playwright/territorial_filters/`.

---

## ☁️ Conexión y Despliegue en Posit Cloud / Posit Connect

El repositorio está configurado y optimizado para conectarse de manera directa con **Posit Cloud** o **Posit Connect**:

1. **Vincular en Posit Cloud:**
   - En su espacio de trabajo de Posit Cloud, seleccione **New Project** -> **New Project from Git Repository**.
   - Ingrese la URL del repositorio: `https://github.com/juanjo-edm/Riesgo_LAFT.git`.
   - Posit Cloud clonará el proyecto e instalará automáticamente el entorno usando el archivo `requirements.txt` universal provisto.

2. **Despliegue Continuo (Git-backed en Posit Connect):**
   - El archivo `manifest.json` en la raíz define el entorno (`python-shiny`, entrypoint `app.py`, Python 3.11/pip), permitiendo que Posit Connect compile y actualice la aplicación automáticamente cada vez que se realice un `push` a la rama `main`.
   - Para regenerar el manifiesto tras añadir librerías o activos:
     ```bash
     uv run rsconnect write-manifest shiny . --overwrite -x "Data/PERSONAS_DEMOGRAFICO_Cuadros_CNPV_2018.xlsx" -x "notebook_methodology/.quarto/*" -x "Output/playwright/*" -x "Output/screenshots/*" -x "*.pyc" -x ".DS_Store" -x ".Rhistory"
     ```

---

## 📖 Cuaderno Metodológico (Quarto)

El cuaderno técnico se encuentra en `notebook_methodology/metodologia.qmd`. Integra la fundamentación jurídica (Código Penal art. 323, SARLAFT, GAFI), extracción reproducible desde la API Socrata (`SoQL` con cobertura municipal completa), justificación matemática y ejecución en Python de todo el pipeline con rutas portables vía `pyprojroot`.

Para compilarlo a HTML interactivo:

```bash
quarto render notebook_methodology/metodologia.qmd
cp notebook_methodology/metodologia.html www/metodologia.html
```

El reporte compilado se genera en `notebook_methodology/metodologia.html` y se sirve en la aplicación desde `www/metodologia.html`.

---

## 🔄 Actualización de Datos (ETL)

Si se actualiza el archivo maestro `Output/atlas_territorial_publico.xlsx`:

```bash
uv run python src/prepare_data.py
```

Este script regenera los archivos optimizados `.parquet` en `Data/processed/`.

---

## 📊 Dimensiones del Atlas

El atlas desagrega el riesgo en **13 dimensiones territoriales**:

1. **`CONT`** - Contrabando y economías ilícitas
2. **`CORR`** - Corrupción pública
3. **`AMBI`** - Delitos ambientales
4. **`EXTC`** - Extorsión y secuestro
5. **`MIEX`** - Minería ilegal
6. **`NARC`** - Narcotráfico
7. **`TFT`** - Terrorismo y eventos asociados
8. **`TRAT`** - Trata y migración irregular
9. **`HURTO`** - Hurto (personas, residencias, comercio, vehículos, bancos)
10. **`HOMICIDIOS`** - Homicidios
11. **`VIOLENCIA_SEXUAL`** - Violencia sexual
12. **`ARMAS`** - Incautación de armas de fuego
13. **`CAPTURAS`** - Operatividad policial y capturas
