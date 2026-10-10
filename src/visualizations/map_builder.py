"""
Constructor de mapas coropléticos interactivos con ipyleaflet para Shiny for Python.
Diseño moderno de Geospatial Intelligence con CartoDB Positron, estilos vectoriales
optimizados, info-box en tiempo real y soporte de selección por clic.
"""

from typing import Any, Callable, Dict, Optional
import math
import json
import geopandas as gpd
import ipyleaflet
import ipywidgets as widgets
import pandas as pd

from src.config import INTENSIDAD_PALETTE, INTENSIDAD_LEVELS

COLOMBIA_CENTER = [4.1500, -73.2000]
DEFAULT_ZOOM = 5


def padded_bounds(bounds, margin: float = 0.10) -> list[list[float]]:
    """Límites Leaflet con margen por lado, calculados antes de simplificar."""
    west, south, east, north = map(float, bounds)
    dx = max(east - west, 0.01) * margin
    dy = max(north - south, 0.01) * margin
    return [[south - dy, west - dx], [north + dy, east + dx]]


def viewport_for_bounds(bounds, width: float, height: float):
    """Encuadre Web Mercator equivalente a fitBounds, sin rondas de zoom."""
    (south, west), (north, east) = bounds

    def mercator_y(lat):
        radians = math.radians(max(-85.0511, min(85.0511, lat)))
        return math.log(math.tan(math.pi / 4 + radians / 2))

    y_south, y_north = mercator_y(south), mercator_y(north)
    x_span = max((east - west) / 360, 1e-9)
    y_span = max((y_north - y_south) / (2 * math.pi), 1e-9)
    zoom = math.floor(math.log2(min(width / (256 * x_span), height / (256 * y_span))))
    center_lat = math.degrees(2 * math.atan(math.exp((y_south + y_north) / 2)) - math.pi / 2)
    return [center_lat, (west + east) / 2], max(1, min(18, zoom))


def frame_map(m: ipyleaflet.Map, bounds) -> bool:
    """Aplicar el último encuadre en una sola actualización, una vez montado."""
    if bounds is None:
        m.center = COLOMBIA_CENTER
        m.zoom = DEFAULT_ZOOM
        return True
    if not m.pixel_bounds:
        return False
    (left, top), (right, bottom) = m.pixel_bounds
    if right <= left or bottom <= top:
        return False
    center, zoom = viewport_for_bounds(bounds, right - left, bottom - top)
    with m.hold_sync():
        m.center = center
        m.zoom = zoom
    return True


def viewport_has_arrived(m: ipyleaflet.Map, center, zoom) -> bool:
    """Comprobar el encuadre confirmado por Leaflet, no solo el solicitado."""
    if not m.bounds or not m.pixel_bounds:
        return False
    (left, top), (right, bottom) = m.pixel_bounds
    width, height = right - left, bottom - top
    if width <= 0 or height <= 0:
        return False
    (south, west), (north, east) = m.bounds
    degrees_per_pixel = 360 / (256 * 2 ** zoom)
    actual_center, _ = viewport_for_bounds(m.bounds, width, height)
    return (
        abs(east - west - width * degrees_per_pixel) < 2 * degrees_per_pixel
        and abs(actual_center[0] - center[0]) < 2 * degrees_per_pixel
        and abs(actual_center[1] - center[1]) < 2 * degrees_per_pixel
    )


def format_initial_info_box() -> str:
    """HTML inicial elegante para el panel de información cartográfica."""
    return (
        '<div style="background: rgba(255, 255, 255, 0.96); backdrop-filter: blur(8px); '
        'padding: 12px 16px; border-radius: 10px; box-shadow: 0 4px 18px rgba(15, 23, 42, 0.12); '
        'border: 1px solid #E2E8F0; font-family: -apple-system, BlinkMacSystemFont, \'Inter\', sans-serif; '
        'min-width: 220px; max-width: 270px;">'
        '<div style="font-size: 10px; text-transform: uppercase; font-weight: 700; color: #315EEA; letter-spacing: 0.6px; margin-bottom: 2px;">Explorador Cartográfico</div>'
        '<div style="font-size: 12px; font-weight: 600; color: #17253B; margin-bottom: 2px;">Pase el cursor o haga clic</div>'
        '<div style="font-size: 11px; color: #64748B;">Explore indicadores de riesgo por territorio.</div>'
        '</div>'
    )


def format_feature_info_html(
    p: Dict[str, Any],
    join_key: str,
    vista: str,
    score_col: str,
    risk_col: str,
    is_pinned: bool = False,
) -> str:
    """Genera la ficha HTML flotante con los datos del territorio bajo el cursor o fijado por clic."""
    nombre = p.get("nom_mpio") or p.get("dpto") or "Territorio"
    depto = p.get("dpto", "")
    code_val = p.get(join_key, "")
    score_val = p.get(score_col, 0.0)
    score_fmt = f"{score_val:.2f}" if isinstance(score_val, (int, float)) else str(score_val)
    riesgo = p.get(risk_col, "N/A")
    badge_color = INTENSIDAD_PALETTE.get(riesgo, "#64748B")

    pob_val = p.get("poblacion_total") or p.get("poblacion_total_depto")
    pob_str = f"{pob_val:,.0f}".replace(",", ".") if isinstance(pob_val, (int, float)) else "N/A"

    badge_status = (
        '<div style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #315EEA; letter-spacing: 0.5px; margin-bottom: 3px;">📍 Selección fijada</div>'
        if is_pinned
        else '<div style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748B; letter-spacing: 0.5px; margin-bottom: 3px;">Detalle territorial</div>'
    )

    depto_line = (
        f'<div style="font-size: 11px; color: #64748B; margin-bottom: 2px;">{depto} • DIVIPOLA {code_val}</div>'
        if vista == "Municipios" and depto
        else f'<div style="font-size: 11px; color: #64748B; margin-bottom: 2px;">Código DIVIPOLA {code_val}</div>'
    )

    mpios_line = (
        f'<div style="font-size: 11px; color: #64748B; margin-bottom: 2px;">Municipios evaluados: {p.get("municipios_total", "")}</div>'
        if vista == "Departamentos" and "municipios_total" in p
        else ""
    )

    text_color = "#17253B" if riesgo in ["Medio", "Bajo"] else "#FFFFFF"

    return (
        f'<div style="background: rgba(255, 255, 255, 0.97); backdrop-filter: blur(10px); padding: 12px 16px; '
        f'border-radius: 10px; box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14); border: 1px solid #E2E8F0; '
        f'font-family: -apple-system, BlinkMacSystemFont, \'Inter\', sans-serif; min-width: 230px; max-width: 290px;">'
        f'{badge_status}'
        f'<div style="font-size: 13.5px; font-weight: 800; color: #14243A; line-height: 1.2; margin-bottom: 2px;">{nombre}</div>'
        f'{depto_line}'
        f'{mpios_line}'
        f'<div style="margin: 8px 0; padding: 6px 0; border-top: 1px solid #F1F5F9; border-bottom: 1px solid #F1F5F9; '
        f'display: flex; align-items: center; justify-content: space-between;">'
        f'<span style="font-size: 11.5px; color: #334155;"><b>Índice Activo:</b> {score_fmt}</span>'
        f'<span style="font-size: 11px; font-weight: 700; color: {text_color}; background: {badge_color}; '
        f'padding: 2.5px 8px; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.08);">{riesgo}</span>'
        f'</div>'
        f'<div style="font-size: 11px; color: #64748B; display: flex; justify-content: space-between; align-items: center;">'
        f'<span>Población (DANE 2018):</span>'
        f'<b style="color: #17253B;">{pob_str}</b>'
        f'</div>'
        f'</div>'
    )


def prepare_geojson_data(
    geodata: Optional[gpd.GeoDataFrame],
    data: pd.DataFrame,
    join_key: str,
    vista: str = "Municipios",
    score_col: str = "score_activo",
    risk_col: str = "riesgo_activo",
    selected_code: Optional[str] = None,
) -> tuple[Optional[Dict[str, Any]], Optional[Any]]:
    """Prepara y estiliza las geometrías GeoJSON para la capa territorial."""
    if geodata is None or geodata.empty or data.empty:
        return None, None

    merged = geodata.merge(data, on=join_key, how="inner")
    if merged.empty:
        return None, None

    if merged.crs is not None and merged.crs.to_epsg() != 4326:
        merged = merged.to_crs(epsg=4326)

    merged = merged[merged.geometry.apply(lambda geometry: geometry is not None and not geometry.is_empty)].copy()
    if merged.empty:
        return None, None
    selected = merged[merged[join_key].astype(str) == str(selected_code)] if selected_code else merged.iloc[:0]
    has_selection = not selected.empty
    bounds = padded_bounds(selected.total_bounds if has_selection else merged.total_bounds)

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

    if vista == "Municipios" and len(sub_gdf) > 100:
        neighbors = sub_gdf[join_key].astype(str) != str(selected_code)
        sub_gdf.loc[neighbors, "geometry"] = sub_gdf.loc[neighbors, "geometry"].simplify(0.005, preserve_topology=True)

    default_border = "#334155" if vista == "Departamentos" else "#94A3B8"
    default_weight = 1.0 if vista == "Departamentos" else 0.55

    styles_list = []
    for _, row in sub_gdf.iterrows():
        code = str(row.get(join_key, ""))
        is_sel = has_selection and code == str(selected_code)
        risk = row.get(risk_col, "Bajo")

        if is_sel:
            styles_list.append(
                {
                    "fillColor": INTENSIDAD_PALETTE.get(risk, "#8BC34A"),
                    "color": "#315EEA",
                    "weight": 2.6,
                    "fillOpacity": 0.88,
                    "opacity": 1.0,
                }
            )
        else:
            styles_list.append(
                {
                    "fillColor": INTENSIDAD_PALETTE.get(risk, "#8BC34A"),
                    "color": default_border,
                    "weight": default_weight,
                    "fillOpacity": 0.0 if has_selection else 0.76,
                    "opacity": 0.85,
                }
            )

    sub_gdf["style"] = styles_list
    geojson_dict = json.loads(sub_gdf.to_json())
    return geojson_dict, bounds


def update_ipyleaflet_map(
    m: ipyleaflet.Map,
    geodata: Optional[gpd.GeoDataFrame],
    data: pd.DataFrame,
    join_key: str,
    vista: str = "Municipios",
    score_col: str = "score_activo",
    risk_col: str = "riesgo_activo",
    selected_code: Optional[str] = None,
    fit_view: bool = True,
) -> Optional[Any]:
    """Actualiza las capas y el encuadre territorial in situ sin reconstruir el widget."""
    geojson_dict, bounds = prepare_geojson_data(
        geodata=geodata,
        data=data,
        join_key=join_key,
        vista=vista,
        score_col=score_col,
        risk_col=risk_col,
        selected_code=selected_code,
    )

    geo_layer = None
    for layer in m.layers:
        if isinstance(layer, ipyleaflet.GeoJSON):
            geo_layer = layer
            break

    if geo_layer is not None:
        geo_layer.hover_style = {"weight": 2.2}
        generation = getattr(geo_layer, "_atlas_generation", 0) + 1
        geo_layer._atlas_generation = generation
        if geojson_dict:
            for feature in geojson_dict["features"]:
                feature["properties"]["_atlas_generation"] = generation
            geo_layer.data = geojson_dict
            geo_layer.name = f"Capa {vista}"
        else:
            geo_layer.data = {"type": "FeatureCollection", "features": []}

    if fit_view:
        frame_map(m, bounds)
    return bounds


def build_ipyleaflet_map(
    geodata: Optional[gpd.GeoDataFrame],
    data: pd.DataFrame,
    join_key: str,
    vista: str = "Municipios",
    score_col: str = "score_activo",
    risk_col: str = "riesgo_activo",
    selected_code: Optional[str] = None,
    on_hover_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_select_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
) -> ipyleaflet.Map:
    """
    Construye un mapa interactivo ipyleaflet con coropleta vectorial según el nivel
    de riesgo territorial, mapa base limpio y confiable, y controles enriquecidos.
    """
    basemap = ipyleaflet.basemaps.Esri.WorldGrayCanvas

    hover_style = {"weight": 2.2}

    geojson_dict, _ = prepare_geojson_data(
        geodata=geodata,
        data=data,
        join_key=join_key,
        vista=vista,
        score_col=score_col,
        risk_col=risk_col,
        selected_code=selected_code,
    )

    geo_layer = ipyleaflet.GeoJSON(
        data=geojson_dict or {"type": "FeatureCollection", "features": []},
        style_callback=lambda feat: feat.get("properties", {}).get("style", {}),
        hover_style=hover_style,
        name=f"Capa {vista}",
    )

    def on_feature_hover(event=None, feature=None, **kwargs):
        if not feature or "properties" not in feature:
            return
        p = feature["properties"]
        # Descartar eventos en tránsito de una capa anterior (especialmente al
        # desplazar o acercar el mapa en pantallas táctiles).
        if p.get("_atlas_generation", 0) != getattr(geo_layer, "_atlas_generation", 0):
            return
        coordinates = kwargs.get("coordinates")
        if coordinates and m.bounds:
            (south, west), (north, east) = m.bounds
            lat, lon = coordinates
            if not (south <= lat <= north and west <= lon <= east):
                return
        if on_hover_callback:
            on_hover_callback(p)

    def on_feature_click(event=None, feature=None, **kwargs):
        if not feature or "properties" not in feature:
            return
        p = feature["properties"]
        if p.get("_atlas_generation", 0) != getattr(geo_layer, "_atlas_generation", 0):
            return
        feat_id = str(p.get("cod_mpio") or p.get("cod_dpto") or p.get(join_key, ""))
        if on_select_callback:
            on_select_callback(feat_id, p)

    geo_layer.on_hover(on_feature_hover)
    geo_layer.on_click(on_feature_click)

    m = ipyleaflet.Map(
        center=COLOMBIA_CENTER,
        zoom=DEFAULT_ZOOM,
        basemap=basemap,
        scroll_wheel_zoom=True,
        attribution_control=True,
        layout=widgets.Layout(height="580px", width="100%"),
    )

    m.add(ipyleaflet.ScaleControl(position="bottomleft"))
    m.add(ipyleaflet.FullScreenControl())

    legend_items = {level: INTENSIDAD_PALETTE[level] for level in INTENSIDAD_LEVELS}
    legend = ipyleaflet.LegendControl(
        legend=legend_items,
        title="Intensidad LAFT",
        position="bottomright",
    )
    m.add(legend)
    m.add(geo_layer)

    return m
