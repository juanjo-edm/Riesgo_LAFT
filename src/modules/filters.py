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
def filters_ui():
    return ui.TagList(
        ui.input_select(
            "vista",
            "Vista territorial",
            choices=["Municipios", "Departamentos"],
            selected="Municipios",
        ),
        ui.input_select(
            "departamento",
            "Departamento",
            choices=["Todos"],
            selected="Todos",
        ),
        ui.panel_conditional(
            "input.vista === 'Municipios'",
            ui.input_select(
                "municipio",
                "Municipio para perfil",
                choices={"":"Seleccione..."},
                selected="",
            ),
        ),
        ui.tags.hr(style="margin: 12px 0; border-color: #cbd5e1;"),
        ui.input_checkbox_group(
            "dimensiones",
            "Dimensiones de análisis",
            choices={dim: DIMENSION_LABELS.get(dim, dim) for dim in DIMENSIONES_TERRITORIALES},
            selected=[],
        ),
        ui.input_checkbox_group(
            "fuentes",
            "Fuentes e indicadores específicos",
            choices={},
            selected=[],
        ),
        ui.tags.hr(style="margin: 12px 0; border-color: #cbd5e1;"),
        ui.input_checkbox_group(
            "niveles",
            "Niveles de intensidad",
            choices=INTENSIDAD_LEVELS,
            selected=INTENSIDAD_LEVELS,
        ),
        ui.input_action_button(
            "clear_filters",
            "Borrar todos los filtros",
            class_="btn-outline-secondary w-100 mt-2",
        ),
    )


@module.server
def filters_server(input, output, session, data: Dict[str, pd.DataFrame]):
    municipios_df = data["municipios"]
    catalogo_df = data["catalogo_indicadores"]

    # Poblar departamentos en el select
    @reactive.effect
    def _init_departamentos():
        deptos = ["Todos"] + sorted(municipios_df["dpto"].dropna().unique().tolist())
        ui.update_select("departamento", choices=deptos, selected="Todos")

    # Actualizar municipios según departamento seleccionado
    @reactive.effect
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
        selected_val = current_val if current_val in mpios_dict else ""
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
