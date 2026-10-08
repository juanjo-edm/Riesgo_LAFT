"""
Constructor de mapas coropléticos interactivos con ipyleaflet para Shiny for Python.
"""

from typing import Any, Dict, Optional
import json
import geopandas as gpd
import ipyleaflet
import ipywidgets as widgets
import pandas as pd

from src.config import INTENSIDAD_PALETTE, INTENSIDAD_LEVELS

COLOMBIA_CENTER = [4.5709, -74.2973]
DEFAULT_ZOOM = 6


def build_ipyleaflet_map(
    geodata: Optional[gpd.GeoDataFrame],
    data: pd.DataFrame,
    join_key: str,
    vista: str = "Municipios",
    score_col: str = "score_activo",
    risk_col: str = "riesgo_activo",
) -> ipyleaflet.Map:
    """
    Construye un mapa interactivo ipyleaflet con coropleta vectorial según el nivel
    de riesgo territorial y controles enriquecidos de navegación.
    """
    # Crear instancia nueva de Map para cada sesión con renderizado Canvas de alto desempeño
    m = ipyleaflet.Map(
        center=COLOMBIA_CENTER,
        zoom=DEFAULT_ZOOM,
        basemap=ipyleaflet.basemaps.OpenStreetMap.Mapnik,
        scroll_wheel_zoom=True,
        attribution_control=True,
        prefer_canvas=True,
    )

    # Controles de navegación y escala estándar
    m.add(ipyleaflet.ScaleControl(position="bottomleft"))
    m.add(ipyleaflet.FullScreenControl())

    # Leyenda temática fija
    legend_items = {level: INTENSIDAD_PALETTE[level] for level in INTENSIDAD_LEVELS}
    legend = ipyleaflet.LegendControl(
        legend=legend_items,
        title="Intensidad LAFT",
        position="bottomright",
    )
    m.add(legend)

    # Control de información interactivo tipo Info Box (topright)
    info_widget = widgets.HTML(
        value="""<div style="background: rgba(255, 255, 255, 0.95); padding: 10px 14px; border-radius: 8px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15); border: 1px solid #cbd5e1; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; min-width: 210px;">
        <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #4338ca; letter-spacing: 0.5px;">Detalle Territorial</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Pase el cursor sobre un polígono</div>
    </div>"""
    )
    info_control = ipyleaflet.WidgetControl(widget=info_widget, position="topright")
    m.add(info_control)

    if geodata is None or geodata.empty or data.empty:
        info_widget.value = (
            '<div style="background: rgba(255, 255, 255, 0.95); padding: 10px 14px; '
            'border-radius: 8px; border: 1px solid #f59e0b; font-family: sans-serif; font-size: 12px; '
            'color: #b45309;">⚠️ Sin datos territoriales para el filtro seleccionado.</div>'
        )
        return m

    # Merge de geometrías con los datos activos filtrados
    merged = geodata.merge(data, on=join_key, how="inner")
    if merged.empty:
        info_widget.value = (
            '<div style="background: rgba(255, 255, 255, 0.95); padding: 10px 14px; '
            'border-radius: 8px; border: 1px solid #f59e0b; font-family: sans-serif; font-size: 12px; '
            'color: #b45309;">⚠️ Ningún territorio coincide con los filtros aplicados.</div>'
        )
        return m

    # Asegurar proyección WGS84
    if merged.crs is not None and merged.crs.to_epsg() != 4326:
        merged = merged.to_crs(epsg=4326)

    # Ajustar centro y viewport dinámicamente si es un subconjunto
    bounds = merged.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2.0
    center_lon = (bounds[0] + bounds[2]) / 2.0
    m.center = [center_lat, center_lon]

    # Si es un departamento específico o vista filtrada pequeña, ajustar vista
    lat_span = bounds[3] - bounds[1]
    lon_span = bounds[2] - bounds[0]
    if lat_span < 5.0 or lon_span < 5.0:
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Seleccionar únicamente columnas requeridas para optimizar el payload GeoJSON
    cols = ["geometry", join_key, score_col, risk_col]
    if "nom_mpio" in merged.columns:
        cols.append("nom_mpio")
    if "dpto" in merged.columns:
        cols.append("dpto")
    pob_col = "poblacion_total" if "poblacion_total" in merged.columns else "poblacion_total_depto"
    if pob_col in merged.columns:
        cols.append(pob_col)
    if "municipios_total" in merged.columns:
        cols.append("municipios_total")

    sub_gdf = merged[[c for c in cols if c in merged.columns or c == "geometry"]].copy()

    # Precomputar estilos directamente en el DataFrame para evitar deepcopy y bucles lentos
    border_color = "#334155" if vista == "Departamentos" else "#64748b"
    border_weight = 1.2 if vista == "Departamentos" else 0.6
    sub_gdf["style"] = [
        {
            "fillColor": INTENSIDAD_PALETTE.get(r, "#8BC34A"),
            "color": border_color,
            "weight": border_weight,
            "fillOpacity": 0.75,
            "opacity": 0.85,
        }
        for r in sub_gdf[risk_col]
    ]

    # Convertir a diccionario GeoJSON optimizado
    geojson_dict = json.loads(sub_gdf.to_json())

    # Estilo al pasar el cursor (hover)
    hover_style = {
        "fillColor": "#1e1b4b",
        "color": "#0f172a",
        "weight": 2.2,
        "fillOpacity": 0.9,
    }

    geo_layer = ipyleaflet.GeoJSON(
        data=geojson_dict,
        hover_style=hover_style,
        name=f"Capa {vista}",
    )

    # Actualización interactiva del Info Box en hover con deduplicación por ID territorial
    last_hovered_id = [None]

    def on_feature_hover(event=None, feature=None, **kwargs):
        if not feature or "properties" not in feature:
            return

        p = feature["properties"]
        feat_id = p.get(join_key)
        if feat_id is not None and feat_id == last_hovered_id[0]:
            return
        last_hovered_id[0] = feat_id

        nombre = p.get("nom_mpio") or p.get("dpto") or "Territorio"
        depto = p.get("dpto", "")
        score_val = p.get(score_col, 0.0)
        score_fmt = f"{score_val:.2f}" if isinstance(score_val, (int, float)) else str(score_val)
        riesgo = p.get(risk_col, "N/A")
        badge_color = INTENSIDAD_PALETTE.get(riesgo, "#64748b")

        pob_val = p.get("poblacion_total") or p.get("poblacion_total_depto")
        pob_str = f"{pob_val:,.0f}".replace(",", ".") if isinstance(pob_val, (int, float)) else "N/A"

        depto_line = (
            f'<div style="font-size: 11px; color: #64748b; margin-bottom: 2px;">Depto: {depto}</div>'
            if vista == "Municipios" and depto
            else ""
        )
        mpios_line = (
            f'<div style="font-size: 11px; color: #64748b; margin-bottom: 2px;">Municipios evaluados: {p.get("municipios_total", "")}</div>'
            if vista == "Departamentos" and "municipios_total" in p
            else ""
        )

        info_widget.value = f"""<div style="background: rgba(255, 255, 255, 0.98); padding: 10px 14px; border-radius: 8px; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.18); border: 1px solid #cbd5e1; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; min-width: 220px;">
        <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 2px;">{nombre}</div>
        {depto_line}
        {mpios_line}
        <div style="margin: 6px 0; display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 12px; color: #334155;"><b>Índice Activo:</b> {score_fmt}</span>
            <span style="font-size: 11px; font-weight: 700; color: #ffffff; background: {badge_color}; padding: 2px 8px; border-radius: 10px;">{riesgo}</span>
        </div>
        <div style="font-size: 11px; color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 4px;">Población: {pob_str} habs.</div>
    </div>"""

    geo_layer.on_hover(on_feature_hover)
    m.add(geo_layer)

    return m
