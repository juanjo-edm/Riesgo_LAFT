# Atlas Territorial de Problemáticas en Colombia (Medición de Riesgo LAFT)

Este repositorio consolida fuentes públicas territoriales para explorar, comparar y visualizar problemáticas municipales y departamentales en Colombia y su asociación al riesgo de **Lavado de Activos y Financiación del Terrorismo (LA/FT)**.

El flujo procesa datos abiertos oficiales (vía API SoQL y bases institucionales), calcula tasas por 100.000 habitantes estandarizadas con z-scores, aplica winsorización robusta (1%–99%), estima pesos objetivos mediante **CRITIC** (*Criteria Importance Through Intercriteria Correlation*), clasifica municipios y departamentos con **K-Means ($k=4$)** y publica una aplicación interactiva en **Shiny for Python (`shiny`)** con mapas vectoriales reactivos en **ipyleaflet**, componentes modernos **bslib** (`value_box`, tarjetas adaptables) y gráficos interactivos en **Plotly**.

---

## 🏛️ Estructura del Proyecto

Siguiendo las mejores prácticas de desarrollo en Python:

```text
├── app.py                      # Entrada principal de la aplicación Shiny for Python
├── manifest.json               # Manifiesto de despliegue para Posit Connect / Posit Cloud
├── pyproject.toml              # Definición de dependencias y configuración de uv (PEP 621)
├── requirements.txt            # Dependencias fijadas para despliegue universal
├── src/                        # Código fuente modular de la aplicación ([Ver Documentación](src/README.md))
│   ├── config.py               # Constantes, paletas y definiciones de dimensiones
│   ├── data_loader.py          # Carga y caché de datos Parquet y geometrías
│   ├── calculator.py           # Recálculo reactivo de scores y K-Means dinámico
│   ├── critic.py               # Algoritmo de ponderación objetiva CRITIC en Python
│   ├── prepare_data.py         # Pipeline ETL de conversión Excel -> Parquet/Geodata
│   ├── components/             # Componentes reutilizables de UI (cards, badges)
│   ├── modules/                # Módulos Shiny ([Ver Documentación](src/modules/README.md))
│   └── visualizations/         # Generadores de mapas ipyleaflet y gráficos Plotly
├── notebook_methodology/       # Cuaderno metodológico en Quarto ([Ver Documentación](notebook_methodology/README.md))
│   ├── data/                   # Insumos primarios del cuaderno
│   ├── images/                 # Gráficos y esquemas
│   ├── metodologia.qmd         # Cuaderno Quarto con motor Python (Jupyter)
│   ├── metodologia.html        # Cuaderno compilado interactivo auto-contenido
│   └── _quarto.yml             # Configuración del documento Quarto
├── data/
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

### Funcionalidades de la Aplicación:
- **🗺️ Mapa Territorial:** Coropleta vectorial reactiva con **ipyleaflet** que colorea los 1.121 municipios o los 33 departamentos según el nivel de riesgo activo, con Info Box interactivo en tiempo real al pasar el cursor, control de escala, controles de pantalla completa y zoom contextual.
- **📊 Rankings:** Tablas interactivas con ordenamiento, filtrado multifactorial, resumen de distribución y exportación a formato CSV.
- **🏛️ Perfil Municipal:** Ficha técnica por municipio con gráfico de telaraña (*spider/radar chart*) interactivo en **Plotly** frente al promedio nacional y tabla detallada de dimensiones.
- **🇨🇴 Perfil Departamental:** Agregación de dimensiones ponderadas por población municipal y diagnóstico departamental.
- **🔄 Recálculo Reactivo en Tiempo Real:** Permite aislar dimensiones específicas o fuentes internas (por ejemplo, analizar únicamente *Cultivos ilícitos* dentro de *Narcotráfico*), reclasificando los niveles de intensidad al vuelo.

---

## ☁️ Conexión y Despliegue en Posit Cloud / Posit Connect

El repositorio está configurado y optimizado para conectarse de manera directa con **Posit Cloud** o **Posit Connect**:

1. **Vincular en Posit Cloud:**
   - En su espacio de trabajo de Posit Cloud, seleccione **New Project** -> **New Project from Git Repository**.
   - Ingrese la URL del repositorio: `https://github.com/juanjo-edm/Riesgo_LAFT.git`.
   - Posit Cloud clonará el proyecto e instalará automáticamente el entorno usando el archivo `requirements.txt` universal provisto.

2. **Despliegue Continuo (Git-backed en Posit Connect):**
   - El archivo `manifest.json` en la raíz define el entorno (`python-shiny`, entrypoint `app.py`, Python 3.11/pip), permitiendo que Posit Connect compile y actualice la aplicación automáticamente cada vez que se realice un `push` a la rama `main`.
   - Para regenerar el manifiesto en el futuro tras añadir librerías:
     ```bash
     uv run rsconnect write-manifest shiny . --overwrite -x "Data/PERSONAS_DEMOGRAFICO_Cuadros_CNPV_2018.xlsx" -x "notebook_methodology/.quarto/*" -x "*.pyc" -x ".DS_Store" -x ".Rhistory"
     ```

---

## 📖 Cuaderno Metodológico (Quarto)

El cuaderno técnico se encuentra en `notebook_methodology/metodologia.qmd`. Integra la fundamentación jurídica (Código Penal art. 323, SARLAFT, GAFI), la justificación teórica y la ejecución en código Python de todo el pipeline.

Para compilarlo a HTML interactivo:

```bash
quarto render notebook_methodology/metodologia.qmd
```

El reporte compilado se genera en `notebook_methodology/metodologia.html`.

---

## 🔄 Actualización de Datos (ETL)

Si se actualiza el archivo maestro `Output/atlas_territorial_publico.xlsx`:

```bash
uv run python src/prepare_data.py
```

Este script regenera los archivos optimizados `.parquet` en `data/processed/`.

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
