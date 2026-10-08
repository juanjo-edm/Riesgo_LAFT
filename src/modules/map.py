"""
Módulo de Mapa Interactivo con Folium para Shiny for Python.
"""

from pathlib import Path
import tempfile
import time
from typing import Any, Dict
import pandas as pd
from shiny import module, reactive, render, ui
from starlette.responses import HTMLResponse

from src.components.cards import metric_card, risk_badge
from src.visualizations.map_builder import build_choropleth_map

# Directorio temporal del sistema (fuera del árbol del proyecto para evitar reload loops con watchfiles)
CACHE_DIR = Path(tempfile.gettempdir()) / "atlas_laft_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_MAP_FILE = CACHE_DIR / "active_map.html"

# Variable global para servir el mapa en memoria ultra rápido
_ACTIVE_MAP_HTML: str = ""


def get_active_map_html_response(request=None) -> HTMLResponse:
    """Retorna el mapa interactivo directamente desde memoria o caché temporal."""
    global _ACTIVE_MAP_HTML
    if not _ACTIVE_MAP_HTML and CACHE_MAP_FILE.exists():
        try:
            _ACTIVE_MAP_HTML = CACHE_MAP_FILE.read_text(encoding="utf-8")
        except Exception:
            pass

    if not _ACTIVE_MAP_HTML:
        placeholder = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;color:#64748b;background:#f8fafc;">
    <div style="text-align:center;">
        <div style="font-size:32px;margin-bottom:12px;">🗺️</div>
        <div style="font-weight:600;font-size:16px;">Generando mapa interactivo...</div>
        <div style="font-size:13px;margin-top:6px;color:#94a3b8;">Sincronizando capas territoriales</div>
    </div>
</body>
</html>"""
        return HTMLResponse(placeholder, media_type="text/html")

    return HTMLResponse(_ACTIVE_MAP_HTML, media_type="text/html")


@module.ui
def map_ui():
    return ui.TagList(
        ui.tags.div(
            ui.output_ui("metrics_summary"),
            style="margin-bottom: 14px;",
        ),
        ui.tags.div(
            ui.output_ui("map_container"),
            style="border-radius: 8px; overflow: hidden; border: 1px solid #cbd5e1; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); min-height: 650px; background: #f8fafc;",
        ),
    )


@module.server
def map_server(
    input,
    output,
    session,
    filtered_data: reactive.Calc,
    geodata: Dict[str, Any],
):
    @output
    @render.ui
    def metrics_summary():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        df = fd["municipios"] if vista == "Municipios" else fd["departamentos"]

        if df.empty:
            return ui.tags.div("No hay territorios que coincidan con los filtros.", class_="alert alert-warning")

        total_territorios = len(df)
        score_promedio = f"{df['score_activo'].mean():.2f}"
        
        # Nivel más frecuente
        modo_riesgo = df["riesgo_activo"].mode()[0] if not df["riesgo_activo"].empty else "N/A"

        # Población
        pob_col = "poblacion_total" if vista == "Municipios" else "poblacion_total_depto"
        pob_total = df[pob_col].sum() if pob_col in df.columns else 0
        pob_str = f"{pob_total:,.0f}".replace(",", ".")

        return ui.layout_columns(
            metric_card("Territorios Visibles", f"{total_territorios}", f"Vista: {vista}"),
            metric_card("Índice Activo Promedio", score_promedio, "Escala relativa"),
            metric_card("Intensidad Predominante", modo_riesgo, "Mayoría territorial"),
            metric_card("Población Cubierta", pob_str, "Habitantes (Censo DANE)"),
            col_widths=[3, 3, 3, 3],
        )

    @output
    @render.ui
    def map_container():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        df = fd["municipios"] if vista == "Municipios" else fd["departamentos"]

        if vista == "Departamentos":
            geo = geodata.get("mapa_departamentos")
            join_key = "cod_dpto"
        else:
            geo = geodata.get("mapa_municipios")
            join_key = "cod_mpio"

        if geo is None or df.empty:
            return ui.tags.div(
                ui.tags.p("Cargando mapa o sin datos para mostrar...", style="color: #64748b; padding: 40px; text-align: center;"),
            )

        # Construir mapa Folium
        folium_map = build_choropleth_map(
            geodata=geo,
            data=df,
            join_key=join_key,
            vista=vista,
            score_col="score_activo",
            risk_col="riesgo_activo",
        )

        # Generar HTML completo y almacenarlo en memoria
        rendered_html = folium_map.get_root().render()
        global _ACTIVE_MAP_HTML
        _ACTIVE_MAP_HTML = rendered_html

        # Guardar en archivo temporal fuera del proyecto como persistencia adicional
        try:
            CACHE_MAP_FILE.write_text(rendered_html, encoding="utf-8")
        except Exception:
            pass

        # Servir el mapa mediante el endpoint HTTP registrado /active_map.html
        timestamp = int(time.time() * 1000)
        return ui.tags.iframe(
            src=f"/active_map.html?t={timestamp}",
            style="width: 100%; height: 650px; border: none; display: block;",
        )
