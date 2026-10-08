"""
Aplicación Principal: Atlas Territorial de Problemáticas en Colombia y Riesgo LAFT.
Framework: Shiny for Python (shiny).
"""

from pathlib import Path
from shiny import App, reactive, ui

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
        title=ui.span(
            ui.span("⚙️", style="margin-right: 6px;"),
            "Panel de Filtros",
            style="font-weight: 800; color: #1e1b4b; letter-spacing: -0.2px;",
        ),
        bg="#f8fafc",
    ),
    ui.tags.head(
        ui.tags.style(
            """
            :root {
                --bs-primary: #1e1b4b;
                --bs-primary-rgb: 30, 27, 75;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
                background-color: #f8fafc;
                color: #0f172a;
            }
            .atlas-header {
                background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 55%, #312e81 100%);
                color: #ffffff;
                padding: 22px 28px;
                border-radius: 12px;
                box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
                margin-bottom: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .atlas-header .header-badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(8px);
                color: #c7d2fe;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.6px;
                padding: 4px 12px;
                border-radius: 9999px;
                margin-bottom: 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .atlas-header h2 {
                margin: 0;
                font-size: 1.6rem;
                font-weight: 800;
                letter-spacing: -0.025em;
                color: #ffffff;
            }
            .atlas-header p {
                margin: 6px 0 0 0;
                font-size: 0.9rem;
                color: #cbd5e1;
                font-weight: 400;
                line-height: 1.45;
                max-width: 850px;
            }
            .nav-tabs {
                border-bottom: 1px solid #e2e8f0;
                gap: 4px;
            }
            .nav-tabs .nav-link {
                color: #64748b;
                font-size: 0.92rem;
                font-weight: 600;
                border: none;
                border-bottom: 3px solid transparent;
                padding: 10px 18px;
                border-radius: 0;
                transition: color 0.15s ease, border-color 0.15s ease;
            }
            .nav-tabs .nav-link:hover {
                color: #1e1b4b;
                border-bottom-color: #cbd5e1;
            }
            .nav-tabs .nav-link.active {
                font-weight: 700;
                color: #1e1b4b !important;
                background: transparent !important;
                border-bottom: 3px solid #4338ca !important;
            }
            .card {
                border: 1px solid #e2e8f0 !important;
                border-radius: 12px !important;
                box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02) !important;
                background-color: #ffffff;
                transition: box-shadow 0.2s ease;
            }
            .card-header {
                background-color: #ffffff !important;
                border-bottom: 1px solid #f1f5f9 !important;
                padding: 14px 18px !important;
            }
            .filter-section .form-label {
                font-size: 0.8rem;
                font-weight: 600;
                color: #475569;
                margin-bottom: 4px;
            }
            .filter-scrollbox {
                max-height: 190px;
                overflow-y: auto;
                padding: 8px 10px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            .filter-scrollbox::-webkit-scrollbar {
                width: 6px;
            }
            .filter-scrollbox::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 4px;
            }
            .bslib-value-box {
                border-radius: 12px !important;
                box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04) !important;
                border: 1px solid #e2e8f0 !important;
            }
            """
        )
    ),
    ui.tags.div(
        ui.tags.div("🛡️ Metodología Multicriterio Oficial • CRITIC v2.0", class_="header-badge"),
        ui.tags.h2("Atlas Territorial de Problemáticas en Colombia"),
        ui.tags.p("Consolidación analítica de fuentes públicas oficiales, tasas estandarizadas por 100.000 habitantes y ponderación objetiva de riesgo LAFT."),
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
    theme=ui.Theme("zephyr"),
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

app = App(app_ui, server)

if __name__ == "__main__":
    app.run(port=8000)

