"""
Módulo de filtros interactivos para la barra lateral (Sidebar) en Shiny for Python.
Arquitectura Geospatial Intelligence con jerarquía clara de filtros principales y avanzados.
"""

from typing import Dict, List, Optional
import pandas as pd
from shiny import module, reactive, render, ui

from src.components.cards import scenario_badge
from src.config import (
    DIMENSIONES_TERRITORIALES,
    DIMENSION_LABELS,
    INTENSIDAD_LEVELS,
    INTENSIDAD_PALETTE,
)


def _municipio_choices(municipios: pd.DataFrame) -> Dict[str, str]:
    return {
        "": "Seleccione...",
        **{
            str(row["cod_mpio"]): f"{row['nom_mpio']} ({row['dpto']})"
            for _, row in municipios.sort_values("nom_mpio").iterrows()
        },
    }


def _selection_options(control: str) -> dict:
    # onOptionSelect también se ejecuta al volver a elegir el valor actual y con
    # el teclado, pero no cuando Shiny actualiza el control programáticamente.
    return {
        "placeholder": f"Escriba para buscar un {control}",
        "maxOptions": 50,
        "create": False,
        "onInitialize": ui.js_eval("""function() {
            const select = this;
            const original = select.onOptionSelect;
            select.onOptionSelect = function(event) {
                const value = $(event.currentTarget).attr('data-value');
                const result = original.apply(this, arguments);
                if (value !== undefined) {
                    const id = select.$input.attr('id');
                    const control = id.endsWith('-departamento') ? 'departamento' : 'municipio';
                    Shiny.setInputValue(id.slice(0, -control.length) + 'territory_selection',
                        {control: control, value: value}, {priority: 'event'});
                }
                return result;
            };
        }"""),
    }


@module.ui
def filters_ui(departamentos: Optional[List[str]] = None, municipios_dict: Optional[Dict[str, str]] = None):
    deptos = departamentos if departamentos is not None else ["Todos"]
    mpios = municipios_dict if municipios_dict is not None else {"": "Seleccione..."}
    selected_mpio = "11001" if "11001" in mpios else ("" if "" in mpios else list(mpios.keys())[0] if mpios else "")

    return ui.TagList(
        # Resumen del escenario activo (Índice General vs Recálculo CRITIC)
        ui.output_ui("scenario_status"),

        # -------------------------------------------------------------
        # 1. FILTROS PRINCIPALES (Ámbito Territorial)
        # -------------------------------------------------------------
        ui.tags.div(
            ui.tags.div(
                ui.tags.span("Ámbito Territorial", class_="filter-section-title"),
                ui.tags.span("Territorios visibles", style="font-size: 0.72rem; color: var(--atlas-text-muted);"),
                class_="d-flex justify-content-between align-items-center mb-1",
            ),
            ui.tags.p(
                "Filtre el universo geográfico visible en mapas, rankings y gráficos.",
                class_="filter-help-text",
            ),
            ui.input_select(
                "vista",
                "Nivel de agregación",
                choices=["Municipios", "Departamentos"],
                selected="Municipios",
            ),
            ui.input_selectize(
                "departamento",
                "Departamento",
                choices=deptos,
                selected="Todos",
                options=_selection_options("departamento"),
            ),
            ui.panel_conditional(
                "input.vista === 'Municipios'",
                ui.input_selectize(
                    "municipio",
                    "Municipio específico",
                    choices=mpios,
                    selected=selected_mpio,
                    options=_selection_options("municipio"),
                ),
            ),
            ui.tags.p(
                "Escriba en Departamento o Municipio para buscar opciones.",
                class_="filter-help-text",
            ),
            class_="filter-section",
        ),

        ui.tags.hr(style="margin: 12px 0; border-color: var(--atlas-border);"),

        # -------------------------------------------------------------
        # 2. FILTROS AVANZADOS (Dimensiones, Indicadores, Intensidad)
        # -------------------------------------------------------------
        ui.tags.div(
            # Acordeón de Dimensiones CRITIC
            ui.tags.details(
                ui.tags.summary(
                    ui.tags.span("📊 Dimensiones de Análisis"),
                    ui.tags.span("▾", style="font-size: 0.9rem; color: var(--atlas-text-muted);"),
                    class_="atlas-disclosure-summary",
                ),
                ui.tags.div(
                    ui.tags.p(
                        "Seleccione dimensiones para recalcular el índice mediante ponderación objetiva CRITIC v2.0 y K-Means dinámico. "
                        "Si no selecciona ninguna, se mantiene el índice global oficial.",
                        class_="filter-help-text",
                    ),
                    ui.tags.div(
                        ui.input_checkbox_group(
                            "dimensiones",
                            None,
                            choices={dim: f"{DIMENSION_LABELS.get(dim, dim)} ({dim})" for dim in DIMENSIONES_TERRITORIALES},
                            selected=[],
                        ),
                        class_="filter-scrollbox",
                    ),
                    # Indicadores específicos dependientes
                    ui.panel_conditional(
                        "input.dimensiones && input.dimensiones.length > 0",
                        ui.tags.div(
                            ui.tags.span("Indicadores específicos disponibles:", style="font-size: 0.78rem; font-weight: 600; color: var(--atlas-text-secondary); display: block; margin: 8px 0 4px 0;"),
                            ui.tags.div(
                                ui.input_checkbox_group(
                                    "fuentes",
                                    None,
                                    choices={},
                                    selected=[],
                                ),
                                class_="filter-scrollbox",
                                style="max-height: 140px;",
                            ),
                        ),
                    ),
                    class_="atlas-disclosure-body",
                ),
                class_="atlas-disclosure",
            ),

            # Acordeón de Niveles de Intensidad
            ui.tags.details(
                ui.tags.summary(
                    ui.tags.span("🎯 Niveles de Intensidad"),
                    ui.tags.span("▾", style="font-size: 0.9rem; color: var(--atlas-text-muted);"),
                    class_="atlas-disclosure-summary",
                ),
                ui.tags.div(
                    ui.tags.p(
                        "Filtre territorios según su clasificación K-Means (k=4).",
                        class_="filter-help-text",
                    ),
                    ui.input_checkbox_group(
                        "niveles",
                        None,
                        choices=INTENSIDAD_LEVELS,
                        selected=INTENSIDAD_LEVELS,
                    ),
                    class_="atlas-disclosure-body",
                ),
                class_="atlas-disclosure",
            ),
            class_="filter-section",
        ),

        # -------------------------------------------------------------
        # 3. ACCIONES DE CONTROL
        # -------------------------------------------------------------
        ui.tags.div(
            ui.input_action_button(
                "clear_filters",
                "Restablecer Filtros",
                class_="btn btn-sm btn-outline-secondary w-100",
                style="font-weight: 600; border-radius: var(--atlas-radius-sm); padding: 7px 12px;",
            ),
            style="margin-top: 14px;",
        ),
        ui.tags.script("""
            document.addEventListener('change', function(event) {
                const select = event.target;
                if (select.tagName === 'SELECT' && select.id.endsWith('-vista')) {
                    Shiny.setInputValue(select.id.slice(0, -5) + 'territory_selection',
                        {control: 'vista', value: select.value}, {priority: 'event'});
                }
            });
        """),
    )


@module.server
def filters_server(input, output, session, data: Dict[str, pd.DataFrame]):
    municipios_df = data["municipios"]
    catalogo_df = data["catalogo_indicadores"]
    map_focus = reactive.Value(None)
    map_revision = reactive.Value(0)

    def focus_territory(nivel=None, codigo=None):
        map_focus.set({"nivel": nivel, "codigo": str(codigo)} if codigo else None)
        with reactive.isolate():
            map_revision.set(map_revision.get() + 1)

    @reactive.effect
    @reactive.event(input.territory_selection)
    def _explicit_selection():
        action = input.territory_selection()
        control, value = action.get("control"), action.get("value")
        if control == "departamento":
            match = data["departamentos"][data["departamentos"]["dpto"] == value]
            if value == "Todos":
                focus_territory()
            elif not match.empty:
                ui.update_select("vista", selected="Departamentos")
                focus_territory("Departamentos", match.iloc[0]["cod_dpto"])
        elif control == "municipio" and input.vista() == "Municipios":
            if value in set(municipios_df["cod_mpio"].astype(str)):
                focus_territory("Municipios", value)
            elif not value:
                focus_territory()
        elif control == "vista":
            focus_territory()

    def select_from_map(code, props):
        if "cod_mpio" in props:
            ui.update_selectize("municipio", selected=code, session=session)
            focus_territory("Municipios", code)
        else:
            ui.update_selectize("departamento", selected=props["dpto"], session=session)
            focus_territory("Departamentos", code)

    # Indicador dinámico de estado del escenario (Índice General vs CRITIC recalculado)
    @output
    @render.ui
    def scenario_status():
        dims = list(input.dimensiones() or [])
        fuentes = list(input.fuentes() or [])
        is_recalc = len(dims) > 0 or len(fuentes) > 0

        if is_recalc:
            count = len(fuentes) if fuentes else len(dims)
            label = f"{len(dims)} dimensión(es)" if dims else f"{len(fuentes)} indicador(es)"
            return scenario_badge(recalculated=True, label=label, active_count=count)
        else:
            return scenario_badge(recalculated=False, label="Índice Global Consolidado")

    # Actualizar municipios únicamente cuando el usuario cambia de departamento
    @reactive.effect
    @reactive.event(input.departamento, ignore_init=True)
    def _update_municipios():
        depto = input.departamento()
        if not depto or depto == "Todos":
            filtered = municipios_df
        else:
            filtered = municipios_df[municipios_df["dpto"] == depto]

        # Mapeo: {cod_mpio: "Nombre (DEPTO)"}
        mpios_dict = _municipio_choices(filtered)

        current_val = input.municipio()
        if current_val in mpios_dict and current_val != "":
            selected_val = current_val
        elif "11001" in mpios_dict:
            selected_val = "11001"
        elif "05001" in mpios_dict:
            selected_val = "05001"
        else:
            first_key = [k for k in mpios_dict if k != ""]
            selected_val = first_key[0] if first_key else ""

        ui.update_selectize("municipio", choices=mpios_dict, selected=selected_val)

    # Actualizar fuentes disponibles según dimensiones seleccionadas
    @reactive.effect
    def _update_fuentes():
        dims = input.dimensiones()
        if not dims:
            ui.update_checkbox_group("fuentes", choices={}, selected=[])
            return

        cat_filtered = catalogo_df[
            catalogo_df["included_in_index"] & catalogo_df["dimension_id"].isin(dims)
        ]
        fuentes_dict = {
            row["source_id"]: f"{row['source_label']} [{row['dimension_id']}]"
            for _, row in cat_filtered.iterrows()
        }

        current_fuentes = [f for f in (input.fuentes() or []) if f in fuentes_dict]
        ui.update_checkbox_group("fuentes", choices=fuentes_dict, selected=current_fuentes)

    # Botón borrar / restablecer filtros a estado inicial limpio
    @reactive.effect
    @reactive.event(input.clear_filters)
    def _clear_all():
        focus_territory()
        ui.update_select("vista", selected="Municipios")
        ui.update_selectize("departamento", selected="Todos")
        mpios_dict = _municipio_choices(municipios_df)
        ui.update_selectize(
            "municipio", choices=mpios_dict, selected="11001" if "11001" in mpios_dict else ""
        )
        ui.update_checkbox_group("dimensiones", selected=[])
        ui.update_checkbox_group("fuentes", selected=[])
        ui.update_checkbox_group("niveles", selected=INTENSIDAD_LEVELS)

    # Devolver estado reactivo de los filtros
    @reactive.calc
    def state():
        return {
            "vista": input.vista() or "Municipios",
            "departamento": input.departamento() or "Todos",
            "municipio": input.municipio() or "",
            "dimensiones": list(input.dimensiones() or []),
            "fuentes": list(input.fuentes() or []),
            "niveles": list(input.niveles() or INTENSIDAD_LEVELS),
        }

    return state, map_focus, map_revision, select_from_map
