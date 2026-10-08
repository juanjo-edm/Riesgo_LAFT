"""
Aplicación Principal: Atlas Territorial de Problemáticas en Colombia y Riesgo LAFT.
Framework: Shiny for Python (shiny).
"""

from pathlib import Path
from shiny import App, reactive, ui

WWW_DIR = Path(__file__).resolve().parent / "www"
WWW_DIR.mkdir(parents=True, exist_ok=True)

from src.calculator import (
    build_department_active,
    build_municipal_active,
    score_to_risk_shared,
)
from src.data_loader import load_app_data
from src.modules.department_profile import (
    department_profile_server,
    department_profile_ui,
)
from src.modules.filters import filters_server, filters_ui
from src.modules.map import map_server, map_ui
from src.modules.profile import profile_server, profile_ui
from src.modules.rankings import rankings_server, rankings_ui

# Cargar datos una sola vez al inicio del proceso
app_data = load_app_data()

app_ui = ui.page_sidebar(
    ui.sidebar(
        filters_ui("filters"),
        width=340,
        title="Filtros y Dimensiones",
    ),
    ui.tags.head(
        ui.tags.style(
            """
            .atlas-header {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background: linear-gradient(135deg, #1e1b4b 0%, #28246f 50%, #312e81 100%);
                color: #ffffff;
                padding: 16px 24px;
                border-bottom: 4px solid #4338ca;
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
                margin: -1.5rem -1.5rem 1.5rem -1.5rem;
                text-align: center;
            }
            .atlas-header h2 {
                margin: 0;
                font-size: 1.45rem;
                font-weight: 800;
                letter-spacing: -0.02em;
            }
            .atlas-header p {
                margin: 4px 0 0 0;
                font-size: 0.85rem;
                color: #c7d2fe;
                font-weight: 400;
            }
            .nav-tabs .nav-link.active {
                font-weight: 700;
                color: #28246f !important;
                border-bottom: 3px solid #28246f !important;
            }
            .nav-tabs .nav-link {
                color: #475569;
                font-size: 0.95rem;
            }
            .card {
                border: 1px solid #e2e8f0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            }
            """
        )
    ),
    ui.tags.div(
        ui.tags.h2("Atlas Territorial de Problemáticas en Colombia"),
        ui.tags.p("Consolidación de fuentes públicas, tasas estandarizadas y ponderación objetiva CRITIC"),
        class_="atlas-header",
    ),
    ui.navset_card_tab(
        ui.nav_panel("🗺️ Mapa Territorial", map_ui("map")),
        ui.nav_panel("📊 Rankings", rankings_ui("rankings")),
        ui.nav_panel("🏛️ Perfil Municipal", profile_ui("profile")),
        ui.nav_panel("🇨🇴 Perfil Departamental", department_profile_ui("department_profile")),
        id="main_tabs",
    ),
    title="Atlas Territorial LAFT Colombia",
    fillable=True,
)


def server(input, output, session):
    filtros = filters_server("filters", app_data)

    @reactive.calc
    def active_scores():
        f = filtros()
        dimensiones = f["dimensiones"]
        fuentes = f["fuentes"]
        recalculate = len(dimensiones) > 0 or len(fuentes) > 0

        municipios = build_municipal_active(
            municipios=app_data["municipios"],
            indicadores=app_data["indicadores_municipales"],
            catalogo=app_data["catalogo_indicadores"],
            dimensiones=dimensiones,
            fuentes=fuentes,
            assign_level=not recalculate,
        )

        departamentos = build_department_active(
            municipios_activos=municipios,
            departamentos=app_data["departamentos"],
            dimensiones=dimensiones,
            fuentes=fuentes,
            assign_level=not recalculate,
        )

        if recalculate:
            municipios, departamentos = score_to_risk_shared(municipios, departamentos)

        return {
            "municipios": municipios,
            "departamentos": departamentos,
        }

    @reactive.calc
    def municipios_active():
        f = filtros()
        datos = active_scores()["municipios"]

        if f["departamento"] != "Todos":
            datos = datos[datos["dpto"] == f["departamento"]]

        if f["niveles"]:
            datos = datos[datos["riesgo_activo"].isin(f["niveles"])]

        return datos

    @reactive.calc
    def departamentos_active():
        f = filtros()
        datos = active_scores()["departamentos"]

        if f["departamento"] != "Todos":
            datos = datos[datos["dpto"] == f["departamento"]]

        if f["niveles"]:
            datos = datos[datos["riesgo_activo"].isin(f["niveles"])]

        return datos

    @reactive.calc
    def filtered_data():
        f = filtros()
        return {
            "municipios": municipios_active(),
            "departamentos": departamentos_active(),
            "vista": f["vista"],
        }

    # Inicializar servidores de módulos
    map_server(
        "map",
        filtered_data=filtered_data,
        geodata={
            "mapa_municipios": app_data["mapa_municipios"],
            "mapa_departamentos": app_data["mapa_departamentos"],
        },
    )

    rankings_server(
        "rankings",
        filtered_data=filtered_data,
    )

    profile_server(
        "profile",
        data=app_data,
        filters_reactive=filtros,
        municipios_active_reactive=municipios_active,
    )

    department_profile_server(
        "department_profile",
        filters_reactive=filtros,
        departamentos_active_reactive=departamentos_active,
        municipios_active_reactive=municipios_active,
    )

app = App(app_ui, server, static_assets=WWW_DIR)

if __name__ == "__main__":
    app.run(port=8000)

