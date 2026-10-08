"""
Módulo de filtros para la barra lateral (Sidebar) en Shiny for Python.
"""

from typing import Dict, List
import pandas as pd
from shiny import module, reactive, ui

from src.config import (
    DIMENSIONES_TERRITORIALES,
    DIMENSION_LABELS,
    INTENSIDAD_LEVELS,
)


@module.ui
def filters_ui(departamentos: List[str] = None, municipios_dict: Dict[str, str] = None):
    deptos = departamentos if departamentos is not None else ["Todos"]
    mpios = municipios_dict if municipios_dict is not None else {"": "Seleccione..."}
    selected_mpio = "11001" if "11001" in mpios else ("" if "" in mpios else list(mpios.keys())[0] if mpios else "")

    return ui.TagList(
        ui.tags.div(
            ui.tags.div(
                ui.tags.span("Ámbito Territorial", style="font-weight: 700; color: #1e1b4b; font-size: 0.9rem; letter-spacing: 0.2px;"),
                style="margin-bottom: 8px; display: flex; align-items: center;",
            ),
            ui.input_select(
                "vista",
                "Nivel de agregación",
                choices=["Municipios", "Departamentos"],
                selected="Municipios",
            ),
            ui.input_select(
                "departamento",
                "Departamento",
                choices=deptos,
                selected="Todos",
            ),
            ui.panel_conditional(
                "input.vista === 'Municipios'",
                ui.input_select(
                    "municipio",
                    "Municipio específico",
                    choices=mpios,
                    selected=selected_mpio,
                ),
            ),
            class_="filter-section mb-3",
        ),
        ui.tags.hr(style="margin: 14px 0; border-color: #e2e8f0;"),
        ui.tags.div(
            ui.tags.div(
                ui.tags.span("Dimensiones de Análisis", style="font-weight: 700; color: #1e1b4b; font-size: 0.9rem; letter-spacing: 0.2px;"),
                style="margin-bottom: 4px; display: flex; align-items: center;",
            ),
            ui.tags.small("Seleccione para recalcular índice con ponderación CRITIC:", style="color: #64748b; font-size: 0.78rem; display: block; margin-bottom: 8px;"),
            ui.tags.div(
                ui.input_checkbox_group(
                    "dimensiones",
                    None,
                    choices={dim: DIMENSION_LABELS.get(dim, dim) for dim in DIMENSIONES_TERRITORIALES},
                    selected=[],
                ),
                class_="filter-scrollbox",
            ),
            ui.tags.div(
                ui.input_checkbox_group(
                    "fuentes",
                    "Indicadores específicos",
                    choices={},
                    selected=[],
                ),
                style="margin-top: 8px;",
            ),
            class_="filter-section mb-3",
        ),
        ui.tags.hr(style="margin: 14px 0; border-color: #e2e8f0;"),
        ui.tags.div(
            ui.tags.div(
                ui.tags.span("Niveles de Intensidad", style="font-weight: 700; color: #1e1b4b; font-size: 0.9rem; letter-spacing: 0.2px;"),
                style="margin-bottom: 8px; display: flex; align-items: center;",
            ),
            ui.input_checkbox_group(
                "niveles",
                None,
                choices=INTENSIDAD_LEVELS,
                selected=INTENSIDAD_LEVELS,
            ),
            class_="filter-section mb-3",
        ),
        ui.input_action_button(
            "clear_filters",
            "Restablecer Filtros",
            class_="btn btn-outline-secondary w-100 mt-2",
        ),
    )


@module.server
def filters_server(input, output, session, data: Dict[str, pd.DataFrame]):
    municipios_df = data["municipios"]
    catalogo_df = data["catalogo_indicadores"]

    # Actualizar municipios únicamente cuando el usuario cambia de departamento
    @reactive.effect
    @reactive.event(input.departamento, ignore_init=True)
    def _update_municipios():
        depto = input.departamento()
        if not depto or depto == "Todos":
            filtered = municipios_df
        else:
            filtered = municipios_df[municipios_df["dpto"] == depto]

        # Mapeo: {cod_mpio: nom_mpio}
        mpios_dict = {"": "Seleccione..."}
        sorted_mpios = filtered.sort_values("nom_mpio")
        for _, row in sorted_mpios.iterrows():
            mpios_dict[str(row["cod_mpio"])] = f"{row['nom_mpio']} ({row['dpto']})"

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

        ui.update_select("municipio", choices=mpios_dict, selected=selected_val)

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

        current_fuentes = [f for f in input.fuentes() if f in fuentes_dict]
        ui.update_checkbox_group("fuentes", choices=fuentes_dict, selected=current_fuentes)

    # Botón borrar filtros
    @reactive.effect
    @reactive.event(input.clear_filters)
    def _clear_all():
        ui.update_select("vista", selected="Municipios")
        ui.update_select("departamento", selected="Todos")
        ui.update_select("municipio", selected="")
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

    return state
