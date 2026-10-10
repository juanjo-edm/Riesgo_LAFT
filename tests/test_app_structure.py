"""
Pruebas de estructura y componentes de la aplicación Shiny for Python.
Verifica que la UI, módulos, visualizaciones y hojas de estilo se carguen
e inicialicen sin errores.
"""

from pathlib import Path
import json
import re
from xml.etree import ElementTree
import pytest
from shiny import App

from src.components.cards import kpi_card, risk_badge, empty_state, method_note, scenario_badge
from src.visualizations.radar import create_radar_chart, create_dimensions_bar_chart, empty_radar_figure
from src.config import DIMENSIONES_TERRITORIALES
from src.modules.filters import filters_ui


def test_app_import_and_instance():
    """Verifica que app.py importe y defina un objeto App válido."""
    import app
    assert isinstance(app.app, App)


def test_css_files_exist():
    """Verifica que todas las hojas de estilo modular existan y no estén vacías."""
    styles_dir = Path("www/styles")
    assert styles_dir.is_dir()

    expected_files = [
        "tokens.css",
        "base.css",
        "layout.css",
        "components.css",
        "map.css",
        "responsive.css",
        "bundle.css",
    ]
    for filename in expected_files:
        filepath = styles_dir / filename
        assert filepath.exists(), f"El archivo {filename} debe existir en www/styles/"
        assert filepath.stat().st_size > 0, f"El archivo {filename} no debe estar vacío"


def test_reusable_cards_components():
    """Verifica renderizado de los componentes de UI."""
    # Badge
    b = risk_badge("Muy alto")
    assert "muy-alto" in str(b)

    # KPI
    k = kpi_card("Territorios", "1.122", unit="mpios")
    assert "1.122" in str(k)

    # Scenario badge
    s_gen = scenario_badge(recalculated=False, label="Índice Global")
    assert "general" in str(s_gen)

    s_rec = scenario_badge(recalculated=True, label="Personalizado", active_count=3)
    assert "recalculated" in str(s_rec)


def test_visualization_builders():
    """Verifica generación de gráficos Plotly para perfiles."""
    target_scores = {dim: 9.0 for dim in DIMENSIONES_TERRITORIALES}
    bench_scores = {dim: 6.0 for dim in DIMENSIONES_TERRITORIALES}

    fig_radar = create_radar_chart(target_scores, "Test", bench_scores)
    assert fig_radar is not None
    assert len(fig_radar.data) == 2

    fig_bars = create_dimensions_bar_chart(target_scores, "Test", bench_scores)
    assert fig_bars is not None
    assert len(fig_bars.data) == 2

    fig_empty = empty_radar_figure()
    assert fig_empty is not None


@pytest.mark.parametrize("target,benchmark", [(0.0, 0.0), (1.0, 6.0), (10.2, 3.0)])
def test_radar_uses_comparable_scale_without_changing_scores(target, benchmark):
    fig = create_radar_chart(
        {dim: target for dim in DIMENSIONES_TERRITORIALES},
        "Territorio",
        {dim: benchmark for dim in DIMENSIONES_TERRITORIALES},
    )

    assert tuple(fig.layout.polar.radialaxis.range) == (0, 12)
    assert fig.layout.polar.radialaxis.tick0 == 0
    assert fig.layout.polar.radialaxis.dtick == 3
    assert [trace.name for trace in fig.data] == ["Promedio Nacional", "Territorio"]
    assert tuple(fig.data[0].r) == (benchmark,) * 14
    assert tuple(fig.data[1].r) == (target,) * 14


def test_territorial_filters_support_search_and_preserve_codes():
    filters = filters_ui(
        "filters",
        departamentos=["Todos", "ANTIOQUIA"],
        municipios_dict={"": "Seleccione...", "11001": "BOGOTÁ, D.C. (BOGOTÁ, D.C.)"},
    )
    markup = ElementTree.fromstring(
        "<root>" + re.sub(r"<script(?![^>]*data-for=)[^>]*>.*?</script>", "", str(filters), flags=re.S) + "</root>"
    )

    department_config = markup.find(".//script[@data-for='filters-departamento']")
    municipality_config = markup.find(".//script[@data-for='filters-municipio']")
    assert department_config is not None
    assert municipality_config is not None
    assert json.loads(department_config.text)["maxOptions"] == 50
    assert json.loads(municipality_config.text)["create"] is False
    assert markup.find(".//option[@value='11001'][@selected]") is not None


def test_build_ipyleaflet_map():
    """Verifica que build_ipyleaflet_map construya una instancia válida de ipyleaflet.Map dentro de una sesión."""
    from unittest.mock import MagicMock
    from shiny.session import session_context
    from shiny._namespaces import Root
    from src.data_loader import load_app_data
    from src.visualizations.map_builder import build_ipyleaflet_map
    import ipyleaflet

    mock_session = MagicMock()
    mock_session.ns = Root
    with session_context(mock_session):
        data = load_app_data()
        m = build_ipyleaflet_map(
            geodata=data["mapa_departamentos"],
            data=data["departamentos"],
            join_key="cod_dpto",
            vista="Departamentos",
            score_col="score_activo",
            risk_col="riesgo_activo",
            selected_code="05",
        )
        assert isinstance(m, ipyleaflet.Map)
        assert m.zoom == 5
        assert len(m.layers) >= 2  # basemap + GeoJSON layer

