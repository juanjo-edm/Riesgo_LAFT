"""
Constructor de mapas coropléticos interactivos con Folium.
"""

from typing import Any, Dict
import folium
import geopandas as gpd
import pandas as pd
from branca.element import MacroElement, Template

from src.config import INTENSIDAD_PALETTE, INTENSIDAD_LEVELS

# Plantilla HTML/CSS para la leyenda flotante
LEGEND_TEMPLATE = """
{% macro html(this, kwargs) %}
<div id="maplegend" class="maplegend" 
     style="position: absolute; z-index: 9999; background-color: rgba(255, 255, 255, 0.92);
            border-radius: 8px; padding: 10px 14px; font-size: 12px; right: 20px; bottom: 25px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <div style="font-weight: 700; margin-bottom: 6px; color: #0f172a; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Intensidad Territorial</div>
  {% for item in this.items %}
    <div style="display: flex; align-items: center; margin-bottom: 4px;">
      <span style="display: inline-block; width: 14px; height: 14px; background: {{ item.color }}; border-radius: 3px; margin-right: 8px; border: 1px solid rgba(0,0,0,0.15);"></span>
      <span style="color: #334155; font-weight: 500;">{{ item.label }}</span>
    </div>
  {% endfor %}
</div>
{% endmacro %}
"""


class LegendElement(MacroElement):
    def __init__(self, items):
        super().__init__()
        self._template = Template(LEGEND_TEMPLATE)
        self.items = items


def build_choropleth_map(
    geodata: gpd.GeoDataFrame,
    data: pd.DataFrame,
    join_key: str,
    vista: str = "Municipios",
    score_col: str = "score_activo",
    risk_col: str = "riesgo_activo",
) -> folium.Map:
    """
    Construye un mapa interactivo Folium con coropleta según el nivel de riesgo territorial.
    """
    # Centro aproximado de Colombia
    colombia_center = [4.5709, -74.2973]
    m = folium.Map(
        location=colombia_center,
        zoom_start=6,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    if geodata is None or geodata.empty or data.empty:
        return m

    # Merge de geometrías con los datos activos
    geo_data_merged = geodata.merge(data, on=join_key, how="inner")
    if geo_data_merged.empty:
        return m

    # Asegurar proyección WGS84 para Folium
    if geo_data_merged.crs is not None and geo_data_merged.crs.to_epsg() != 4326:
        geo_data_merged = geo_data_merged.to_crs(epsg=4326)

    def style_function(feature: Dict[str, Any]) -> Dict[str, Any]:
        props = feature.get("properties", {})
        riesgo = props.get(risk_col, "Bajo")
        fill_color = INTENSIDAD_PALETTE.get(riesgo, "#8BC34A")

        return {
            "fillColor": fill_color,
            "color": "#475569",
            "weight": 0.8 if vista == "Municipios" else 1.5,
            "fillOpacity": 0.75,
            "opacity": 0.9,
        }

    def highlight_function(feature: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "fillColor": "#28246f",
            "color": "#0f172a",
            "weight": 2.2,
            "fillOpacity": 0.9,
        }

    # Definir campos y alias para el tooltip
    if vista == "Departamentos":
        fields = ["dpto", score_col, risk_col, "municipios_total"]
        aliases = ["Departamento:", "Índice:", "Intensidad:", "Municipios:"]
    else:
        fields = ["nom_mpio", "dpto", score_col, risk_col]
        aliases = ["Municipio:", "Departamento:", "Índice:", "Intensidad:"]

    # Filtrar solo campos presentes
    available_fields = [f for f in fields if f in geo_data_merged.columns]
    available_aliases = [aliases[i] for i, f in enumerate(fields) if f in geo_data_merged.columns]

    # Convertir a GeoJSON layer
    geojson_layer = folium.GeoJson(
        geo_data_merged,
        name="Problemáticas Territoriales",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=available_fields,
            aliases=available_aliases,
            localize=True,
            sticky=False,
            style="""
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                color: #0f172a;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 12px;
                padding: 8px 10px;
            """,
        ),
    )
    geojson_layer.add_to(m)

    # Agregar leyenda personalizada
    legend_items = [
        {"label": level, "color": INTENSIDAD_PALETTE[level]} for level in INTENSIDAD_LEVELS
    ]
    m.get_root().add_child(LegendElement(legend_items))

    return m
