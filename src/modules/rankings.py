"""
Módulo de Rankings y Tablas de Posición para Shiny for Python.
"""

from typing import Any, Dict
import io
import pandas as pd
from shiny import module, reactive, render, ui

from src.config import INTENSIDAD_LEVELS, INTENSIDAD_PALETTE
from src.components.cards import method_note


@module.ui
def rankings_ui():
    return ui.TagList(
        ui.output_ui("scale_note"),
        ui.output_ui("summary_cards"),
        ui.tags.div(
            ui.download_button(
                "download_csv",
                "Descargar Tabla (CSV)",
                class_="btn-primary mb-3",
            ),
            style="display: flex; justify-content: flex-end;",
        ),
        ui.tags.div(
            ui.output_data_frame("tabla_ranking"),
            style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);",
        ),
    )


@module.server
def rankings_server(input, output, session, filtered_data: reactive.Calc):
    @output
    @render.ui
    def scale_note():
        return method_note(
            "Los colores clasifican la intensidad mediante K-Means ordenado en 4 niveles (Bajo, Medio, Alto, Muy alto). "
            "El ranking se ordena descendentemente según el índice territorial activo."
        )

    @output
    @render.ui
    def summary_cards():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        df = fd["municipios"] if vista == "Municipios" else fd["departamentos"]

        counts = df["riesgo_activo"].value_counts().to_dict()

        cards = []
        for level in INTENSIDAD_LEVELS:
            count = counts.get(level, 0)
            color = INTENSIDAD_PALETTE.get(level, "#64748b")
            card = ui.tags.div(
                ui.tags.span(level, style="display: block; color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;"),
                ui.tags.strong(f"{count}", style="display: block; color: #0f172a; font-size: 1.3rem; font-weight: 700;"),
                style=f"""
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-top: 4px solid {color};
                    border-radius: 8px;
                    padding: 10px 14px;
                    flex: 1;
                    min-width: 120px;
                """,
            )
            cards.append(card)

        return ui.tags.div(
            *cards,
            style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;",
        )

    @reactive.calc
    def processed_table():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")

        if vista == "Departamentos":
            df = fd["departamentos"].sort_values("score_activo", ascending=False).reset_index(drop=True)
            df["Ranking"] = range(1, len(df) + 1)
            display_df = df[
                ["Ranking", "dpto", "riesgo_activo", "score_activo", "municipios_total", "poblacion_total_depto"]
            ].rename(
                columns={
                    "dpto": "Departamento",
                    "riesgo_activo": "Intensidad",
                    "score_activo": "Índice",
                    "municipios_total": "Municipios",
                    "poblacion_total_depto": "Población",
                }
            )
        else:
            df = fd["municipios"].sort_values("score_activo", ascending=False).reset_index(drop=True)
            df["Ranking"] = range(1, len(df) + 1)
            display_df = df[
                ["Ranking", "nom_mpio", "dpto", "riesgo_activo", "score_activo", "poblacion_total"]
            ].rename(
                columns={
                    "nom_mpio": "Municipio",
                    "dpto": "Departamento",
                    "riesgo_activo": "Intensidad",
                    "score_activo": "Índice",
                    "poblacion_total": "Población",
                }
            )

        display_df["Índice"] = display_df["Índice"].round(2)
        display_df["Población"] = display_df["Población"].apply(lambda x: f"{int(x):,}".replace(",", "."))
        return display_df

    @output
    @render.data_frame
    def tabla_ranking():
        return render.DataGrid(
            processed_table(),
            filters=True,
            selection_mode="none",
            height="550px",
        )

    @render.download_button(filename="ranking_atlas_territorial.csv")
    def download_csv():
        buf = io.StringIO()
        processed_table().to_csv(buf, index=False, encoding="utf-8-sig")
        yield buf.getvalue()
