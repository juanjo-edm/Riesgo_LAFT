"""
Módulo de Mapa Interactivo con ipyleaflet y componentes modernos bslib para Shiny for Python.
"""

from typing import Any, Dict
from faicons import icon_svg
import pandas as pd
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.visualizations.map_builder import build_ipyleaflet_map


@module.ui
def map_ui():
    return ui.TagList(
        ui.tags.div(
            ui.output_ui("metrics_summary"),
            style="margin-bottom: 16px;",
        ),
        ui.card(
            ui.card_header(
                ui.div(
                    ui.div(
                        ui.span(
                            "Distribución Geográfica del Riesgo Territorial",
                            style="font-weight: 700; font-size: 1.05rem; color: #1e1b4b;",
                        ),
                        ui.span(
                            " • Vista interactiva ipyleaflet con ponderación multicriterio",
                            style="font-size: 0.85rem; color: #64748b;",
                        ),
                    ),
                    ui.span(
                        "Interactivo: explore con zoom o pase el cursor para ver detalles",
                        style="font-size: 0.8rem; color: #4338ca; font-weight: 500;",
                    ),
                    class_="d-flex justify-content-between align-items-center w-100 flex-wrap gap-2",
                ),
            ),
            output_widget("territory_map", width="100%", height="650px"),
            full_screen=True,
            min_height="650px",
        ),
    )


@module.server
def map_server(
    input,
    output,
    session,
    filtered_data: reactive.Calc,
    geodata: Dict[str, Any],
):
    @output
    @render.ui
    def metrics_summary():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        df = fd["municipios"] if vista == "Municipios" else fd["departamentos"]

        if df.empty:
            return ui.tags.div(
                "No hay territorios que coincidan con los filtros seleccionados.",
                class_="alert alert-warning",
            )

        total_territorios = f"{len(df):,}".replace(",", ".")
        score_promedio = f"{df['score_activo'].mean():.2f}"

        # Nivel más frecuente
        modo_riesgo = df["riesgo_activo"].mode()[0] if not df["riesgo_activo"].empty else "N/A"

        # Población
        pob_col = "poblacion_total" if vista == "Municipios" else "poblacion_total_depto"
        pob_total = df[pob_col].sum() if pob_col in df.columns else 0
        pob_str = f"{pob_total:,.0f}".replace(",", ".")

        # Tema semántico según nivel predominante
        risk_theme_map = {
            "Muy alto": "danger",
            "Alto": "warning",
            "Medio": "info",
            "Bajo": "success",
        }
        theme_risk = risk_theme_map.get(modo_riesgo, "primary")

        return ui.layout_column_wrap(
            ui.value_box(
                "Territorios Visibles",
                total_territorios,
                f"Vista activa: {vista}",
                showcase=icon_svg("map"),
                theme="primary",
            ),
            ui.value_box(
                "Índice Activo Promedio",
                score_promedio,
                "Escala normalizada [0 - 100]",
                showcase=icon_svg("chart-line"),
                theme="info",
            ),
            ui.value_box(
                "Intensidad Predominante",
                modo_riesgo,
                "Mayoría territorial activa",
                showcase=icon_svg("triangle-exclamation"),
                theme=theme_risk,
            ),
            ui.value_box(
                "Población Cubierta",
                f"{pob_str} hab.",
                "Censo DANE 2018",
                showcase=icon_svg("users"),
                theme="secondary",
            ),
            width="240px",
            fill=False,
        )

    @output
    @render_widget
    def territory_map():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        df = fd["municipios"] if vista == "Municipios" else fd["departamentos"]

        if vista == "Departamentos":
            geo = geodata.get("mapa_departamentos")
            join_key = "cod_dpto"
        else:
            geo = geodata.get("mapa_municipios")
            join_key = "cod_mpio"

        return build_ipyleaflet_map(
            geodata=geo,
            data=df,
            join_key=join_key,
            vista=vista,
            score_col="score_activo",
            risk_col="riesgo_activo",
        )
