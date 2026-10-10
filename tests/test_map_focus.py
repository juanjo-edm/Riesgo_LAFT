"""Enfoque territorial: estilos exclusivos y límites completos del encuadre."""

from unittest.mock import MagicMock
from types import SimpleNamespace

import geopandas as gpd
import ipyleaflet
import pandas as pd
import pytest
from shapely.geometry import MultiPolygon, Polygon, box
from shiny._namespaces import Root
from shiny.session import session_context

from src.config import INTENSIDAD_PALETTE
from src.visualizations.map_builder import (
    build_ipyleaflet_map,
    padded_bounds,
    prepare_geojson_data,
    update_ipyleaflet_map,
    viewport_for_bounds,
    viewport_has_arrived,
)


@pytest.fixture
def territories():
    geo = gpd.GeoDataFrame(
        {"code": ["01", "02"]}, geometry=[box(-75, 4, -74, 6), box(-74, 4, -73, 5)], crs=4326
    )
    data = pd.DataFrame({"code": ["01", "02"], "score_activo": [25.0, 10.0], "riesgo_activo": ["Alto", "Bajo"]})
    return geo, data


@pytest.mark.parametrize("vista", ["Municipios", "Departamentos"])
def test_only_selected_territory_is_filled_and_bounds_have_ten_percent_margin(territories, vista):
    geo, data = territories
    result, bounds = prepare_geojson_data(geo, data, "code", vista, selected_code="01")
    styles = {f["properties"]["code"]: f["properties"]["style"] for f in result["features"]}

    assert styles["01"]["fillColor"] == INTENSIDAD_PALETTE["Alto"]
    assert styles["01"]["color"] == "#315EEA"
    assert styles["01"]["fillOpacity"] == 0.88
    assert styles["02"]["fillOpacity"] == 0
    assert styles["02"]["color"] != "#315EEA"
    assert bounds == [[3.8, -75.1], [6.2, -73.9]]


@pytest.mark.parametrize("selected_code", [None, "missing"])
def test_absent_selection_keeps_general_view_and_risk_fills(territories, selected_code):
    geo, data = territories
    result, bounds = prepare_geojson_data(geo, data, "code", selected_code=selected_code)

    assert bounds == [[3.8, -75.2], [6.2, -72.8]]
    assert all(f["properties"]["style"]["fillOpacity"] == 0.76 for f in result["features"])
    assert all(f["properties"]["style"]["color"] != "#315EEA" for f in result["features"])


def test_encuadre_uses_all_parts_of_selected_geometry(territories):
    geo, data = territories
    geo.loc[0, "geometry"] = MultiPolygon([box(-75, 4, -74, 5), box(-81, 12, -80, 13)])
    _, bounds = prepare_geojson_data(geo, data, "code", selected_code="01")

    assert bounds == [[3.1, -81.7], [13.9, -73.3]]


def test_selected_polygon_is_not_simplified_in_large_layers():
    polygon = Polygon([(0, 0), (0.001, 0.0001), (1, 0), (1, 1), (0, 1)])
    geo = gpd.GeoDataFrame({"code": [str(i) for i in range(101)]}, geometry=[polygon] * 101, crs=4326)
    data = pd.DataFrame({"code": geo.code, "riesgo_activo": "Bajo"})
    result, _ = prepare_geojson_data(geo, data, "code", selected_code="0")

    assert len(result["features"][0]["geometry"]["coordinates"][0]) == 6
    assert len(result["features"][1]["geometry"]["coordinates"][0]) == 5


@pytest.mark.parametrize("empty_geometry", [None, Polygon()])
def test_unavailable_geometry_does_not_activate_exclusive_shading(territories, empty_geometry):
    geo, data = territories
    geo.loc[0, "geometry"] = empty_geometry
    result, _ = prepare_geojson_data(geo, data, "code", selected_code="01")

    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["style"]["fillOpacity"] == 0.76


def test_empty_filtered_universe_has_no_layer_or_bounds(territories):
    geo, data = territories
    assert prepare_geojson_data(geo, data.iloc[:0], "code", selected_code="01") == (None, None)


def test_excluded_selection_shows_remaining_filtered_universe(territories):
    geo, data = territories
    result, bounds = prepare_geojson_data(geo, data.iloc[1:], "code", selected_code="01")

    assert bounds == [[3.9, -74.1], [5.1, -72.9]]
    assert [f["properties"]["code"] for f in result["features"]] == ["02"]
    assert result["features"][0]["properties"]["style"]["fillOpacity"] == 0.76


def test_projected_geometries_are_framed_in_latitude_and_longitude(territories):
    geo, data = territories
    _, bounds = prepare_geojson_data(geo.to_crs(3857), data, "code", selected_code="01")

    assert bounds[0] == pytest.approx([3.8, -75.1])
    assert bounds[1] == pytest.approx([6.2, -73.9])


@pytest.mark.parametrize("size, zoom", [((900, 580), 5), ((330, 580), 4)])
def test_national_panorama_adapts_to_desktop_and_mobile(size, zoom):
    center, actual_zoom = viewport_for_bounds(
        padded_bounds([-81.7356, -4.2294, -66.8485, 13.3945]), *size
    )

    assert actual_zoom == zoom
    assert center[1] == pytest.approx(-74.29205)


@pytest.mark.parametrize("size, expected_zoom", [((900, 580), 9), ((330, 580), 9)])
def test_viewport_fits_complete_bogota_with_margin(size, expected_zoom):
    bounds = padded_bounds([-74.4507, 3.7306, -73.9861, 4.8369])
    center, zoom = viewport_for_bounds(bounds, *size)

    assert center[0] == pytest.approx(4.2840, abs=0.001)
    assert center[1] == pytest.approx(-74.2184)
    assert zoom == expected_zoom


def test_updates_reuse_layer_and_preserve_manual_viewport(territories):
    geo, data = territories
    session = MagicMock()
    session.ns = Root
    with session_context(session):
        m = build_ipyleaflet_map(geo, data, "code", selected_code="01")
        layer = next(layer for layer in m.layers if isinstance(layer, ipyleaflet.GeoJSON))
        m.center, m.zoom = [4.5, -74.5], 11
        update_ipyleaflet_map(m, geo, data.assign(score_activo=99), "code", selected_code="01", fit_view=False)

        assert next(layer for layer in m.layers if isinstance(layer, ipyleaflet.GeoJSON)) is layer
        assert m.center == [4.5, -74.5]
        assert m.zoom == 11
        assert layer.hover_style == {"weight": 2.2}
        assert layer.data["features"][0]["properties"]["score_activo"] == 99


@pytest.mark.parametrize("event", ["mouseover", "click"])
@pytest.mark.parametrize("current_layer, expected", [(False, []), (True, ["02"])])
def test_only_current_layer_events_reach_selection_and_hover_callbacks(territories, event, current_layer, expected):
    geo, data = territories
    observed = []
    session = MagicMock()
    session.ns = Root
    with session_context(session):
        m = build_ipyleaflet_map(
            geo, data, "code",
            on_hover_callback=lambda props: observed.append(props["code"]),
            on_select_callback=lambda code, props: observed.append(code),
        )
        layer = next(layer for layer in m.layers if isinstance(layer, ipyleaflet.GeoJSON))
        previous_feature = layer.data["features"][1]
        update_ipyleaflet_map(m, geo, data, "code", selected_code="01", fit_view=False)
        feature = layer.data["features"][1] if current_layer else previous_feature

        # Mensaje del protocolo ipyleaflet, sin red ni navegador en esta prueba.
        layer._handle_mouse_events(None, {"event": event, "feature": feature}, [])

        assert observed == expected


@pytest.mark.parametrize("center, zoom, arrived", [([4.2834, -74.2195], 9, True), ([4.2834, -74.2195], 8, False), ([7.15, -75.5], 9, False)])
def test_viewport_confirmation_requires_actual_requested_center_and_zoom(center, zoom, arrived):
    # Viewport real de Bogotá, 947 × 580 px, confirmado por Leaflet (zoom 9).
    widget = SimpleNamespace(
        bounds=((3.4887479425, -75.52001953125), (5.0772652945, -72.91900634765)),
        pixel_bounds=((0, 0), (947, 580)),
    )

    assert viewport_has_arrived(widget, center, zoom) is arrived
