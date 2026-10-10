"""
Aplicación Principal: Atlas Territorial de Problemáticas en Colombia y Riesgo LAFT.
Framework: Shiny for Python (shiny).
Diseño: Geospatial Intelligence UI/UX.
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

# Directorio de recursos estáticos www/
WWW_DIR = Path(__file__).resolve().parent / "www"
STYLES_DIR = WWW_DIR / "styles"

# Cargar datos procesados y geometrías una sola vez en el ciclo de vida del proceso
app_data = load_app_data()

deptos_choices = ["Todos"] + sorted(app_data["municipios"]["dpto"].dropna().unique().tolist())
mpios_dict_init = {"": "Seleccione..."}
for _, row in app_data["municipios"].sort_values("nom_mpio").iterrows():
    mpios_dict_init[str(row["cod_mpio"])] = f"{row['nom_mpio']} ({row['dpto']})"

# SVG Icono de Marca (Brújula / Malla Geoespacial)
ATLAS_LOGO_SVG = ui.HTML(
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
    </svg>"""
)

app_ui = ui.page_sidebar(
    # -------------------------------------------------------------------------
    # Panel de Filtros Lateral (Sidebar)
    # -------------------------------------------------------------------------
    ui.sidebar(
        filters_ui("filters", departamentos=deptos_choices, municipios_dict=mpios_dict_init),
        width=330,
        title=ui.span(
            "Configuración y Filtros",
            class_="sidebar-title",
        ),
        bg="#FFFFFF",
    ),

    # -------------------------------------------------------------------------
    # Cabecera HTML y Recursos CSS Modulares
    # -------------------------------------------------------------------------
    ui.tags.head(
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        ui.tags.link(rel="preconnect", href="https://fonts.googleapis.com"),
        ui.tags.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        ui.tags.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap",
        ),
        # Carga modular de estilos desde www/styles/
        ui.tags.link(rel="stylesheet", href="styles/tokens.css"),
        ui.tags.link(rel="stylesheet", href="styles/base.css"),
        ui.tags.link(rel="stylesheet", href="styles/layout.css"),
        ui.tags.link(rel="stylesheet", href="styles/components.css"),
        ui.tags.link(rel="stylesheet", href="styles/map.css"),
        ui.tags.link(rel="stylesheet", href="styles/responsive.css"),
    ),

    # -------------------------------------------------------------------------
    # A. Encabezado Compacto (Sección 5.A)
    # -------------------------------------------------------------------------
    ui.tags.div(
        ui.tags.div(
            ui.tags.div(ATLAS_LOGO_SVG, class_="atlas-brand-logo"),
            ui.tags.div(
                ui.tags.h1("Atlas Territorial LA/FT", class_="atlas-brand-title"),
                ui.tags.p("Inteligencia Geoespacial • Monitoreo Multidimensional de Riesgo en Colombia", class_="atlas-brand-subtitle"),
                class_="atlas-brand-titles",
            ),
            class_="atlas-brand-group",
        ),
        ui.tags.div(
            ui.tags.div(
                ui.tags.span(class_="atlas-status-dot"),
                ui.tags.span("CRITIC v2.0 • K-Means (k=4)"),
                class_="atlas-status-badge",
            ),
            ui.input_action_button(
                "btn_metodologia",
                "Metodología Quarto",
                class_="atlas-methodology-btn",
            ),
            class_="atlas-topbar-actions",
        ),
        class_="atlas-topbar",
    ),

    # -------------------------------------------------------------------------
    # B. Navegación Principal (Sección 5.B)
    # -------------------------------------------------------------------------
    ui.navset_card_tab(
        ui.nav_panel("🗺️ Mapa Territorial", map_ui("map")),
        ui.nav_panel("📊 Rankings y Clasificación", rankings_ui("rankings")),
        ui.nav_panel("🏛️ Perfil Municipal", profile_ui("profile")),
        ui.nav_panel("🇨🇴 Perfil Departamental", department_profile_ui("department_profile")),
        id="main_tabs",
    ),
    title=None,
    window_title="Atlas Territorial LA/FT Colombia",
    theme=ui.Theme("zephyr"),
    fillable=False,
)


def server(input, output, session):
    filtros, map_focus, map_revision, select_from_map = filters_server("filters", app_data)

    # -------------------------------------------------------------------------
    # Modal de Fundamentación Metodológica Quarto
    # -------------------------------------------------------------------------
    @reactive.effect
    @reactive.event(input.btn_metodologia)
    def _show_methodology_modal():
        m = ui.modal(
            ui.tags.div(
                ui.tags.div(
                    ui.tags.p(
                        "El Atlas consolida fuentes públicas oficiales para cuantificar y clasificar el riesgo territorial asociado "
                        "al Lavado de Activos y Financiación del Terrorismo (LA/FT) en los 1.121 municipios y 33 departamentos de Colombia.",
                        style="color: var(--atlas-text-secondary); font-size: 0.92rem; line-height: 1.5; margin-bottom: 14px;",
                    ),
                    ui.tags.div(
                        ui.tags.div(
                            ui.tags.strong("Marco Normativo e Institucional:", style="color: var(--atlas-blue-deep); display: block; margin-bottom: 4px; font-size: 0.86rem;"),
                            ui.tags.p("Código Penal (Art. 323), Recomendaciones GAFI/FATF y estándares SARLAFT de la Superintendencia Financiera.", style="font-size: 0.82rem; margin: 0; color: var(--atlas-text-secondary);"),
                            style="padding: 10px 14px; background: var(--atlas-surface-subtle); border-radius: var(--atlas-radius-sm); border-left: 3px solid var(--atlas-blue-interactive); margin-bottom: 10px;",
                        ),
                        ui.tags.div(
                            ui.tags.strong("Pipeline Estadístico:", style="color: var(--atlas-blue-deep); display: block; margin-bottom: 4px; font-size: 0.86rem;"),
                            ui.tags.ol(
                                ui.tags.li("Tasas estandarizadas por 100.000 habitantes (Censo DANE 2018)."),
                                ui.tags.li("Winsorización robusta (1%–99%) para control de valores extremos."),
                                ui.tags.li("Ponderación objetiva CRITIC (desviación estándar / contraste y correlación intercriterio)."),
                                ui.tags.li("Clasificación K-Means (k=4) ordenada en 4 niveles (Bajo, Medio, Alto, Muy alto)."),
                                style="font-size: 0.82rem; margin: 0; padding-left: 18px; color: var(--atlas-text-secondary); line-height: 1.5;",
                            ),
                            style="padding: 10px 14px; background: var(--atlas-surface-subtle); border-radius: var(--atlas-radius-sm); border-left: 3px solid #10B981; margin-bottom: 14px;",
                        ),
                    ),
                    ui.tags.div(
                        ui.tags.a(
                            "Abrir Documento Metodológico Quarto Completo (HTML) ↗",
                            href="metodologia.html",
                            target="_blank",
                            class_="btn btn-primary w-100",
                            style="font-weight: 600; font-size: 0.88rem; padding: 10px 16px; border-radius: var(--atlas-radius-sm);",
                        ),
                        style="margin-top: 10px;",
                    ),
                ),
            ),
            title="Fundamentación Metodológica y Analítica • CRITIC v2.0",
            size="l",
            easy_close=True,
            footer=ui.modal_button("Cerrar"),
        )
        ui.modal_show(m)

    # -------------------------------------------------------------------------
    # Motor Reactivo de Cálculo (CRITIC v2.0 + K-Means)
    # -------------------------------------------------------------------------
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
            "map_scope": (f["departamento"], tuple(f["niveles"])),
        }

    @reactive.calc
    def selected_territory():
        focus = map_focus()
        fd = filtered_data()
        if not focus or focus["nivel"] != fd["vista"]:
            return None
        municipal = fd["vista"] == "Municipios"
        df = fd["municipios" if municipal else "departamentos"]
        code_col = "cod_mpio" if municipal else "cod_dpto"
        match = df[df[code_col].astype(str) == focus["codigo"]]
        return match.iloc[0].to_dict() if not match.empty else None

    @reactive.effect
    def _remove_excluded_focus():
        focus = map_focus()
        # El cambio automático de nivel se confirma en el cliente en el siguiente
        # ciclo; no descartar durante esa transición la selección departamental.
        if focus and focus["nivel"] == filtros()["vista"] and selected_territory() is None:
            map_focus.set(None)

    # -------------------------------------------------------------------------
    # Inicialización de Servidores de Módulos
    # -------------------------------------------------------------------------
    map_server(
        "map",
        filtered_data=filtered_data,
        geodata={
            "mapa_municipios": app_data["mapa_municipios"],
            "mapa_departamentos": app_data["mapa_departamentos"],
        },
        selected_territory=selected_territory,
        selection_revision=map_revision,
        on_select_callback=select_from_map,
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
