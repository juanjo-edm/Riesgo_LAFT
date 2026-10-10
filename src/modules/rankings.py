"""
Módulo de Rankings y Tablas Clasificatorias para Shiny for Python.
Diseño moderno con DataGrid interactivo, distribución de riesgo por niveles y exportación CSV.
"""

from typing import Any, Dict
import io
import pandas as pd
from shiny import module, reactive, render, ui

from src.components.cards import kpi_card, method_note, risk_badge
from src.config import INTENSIDAD_LEVELS, INTENSIDAD_PALETTE


@module.ui
def rankings_ui():
    return ui.TagList(
        # Nota explicativa
        ui.output_ui("scale_note"),

        # Distribución de territorios por nivel de riesgo
        ui.output_ui("summary_cards"),

        # Tarjeta principal con tabla clasificatoria
        ui.card(
            ui.card_header(
                ui.div(
                    ui.div(
                        ui.h4(
                            "Clasificación General del Riesgo Territorial",
                            style="font-size: 0.98rem; font-weight: 700; color: var(--atlas-blue-deep); margin: 0;",
                        ),
                        ui.p(
                            "Ordenamiento jerárquico descendente según el índice territorial activo",
                            style="font-size: 0.78rem; color: var(--atlas-text-secondary); margin: 2px 0 0 0;",
                        ),
                    ),
                    ui.download_button(
                        "download_csv",
                        "Exportar CSV (Excel UTF-8)",
                        class_="btn btn-sm btn-outline-primary",
                        style="font-weight: 600; font-size: 0.8rem; border-radius: var(--atlas-radius-sm); padding: 5px 12px;",
                    ),
                    class_="d-flex justify-content-between align-items-center w-100 flex-wrap gap-2",
                ),
            ),
            ui.output_data_frame("tabla_ranking"),
            full_screen=True,
            min_height="520px",
        ),
    )


@module.server
def rankings_server(input, output, session, filtered_data: reactive.Calc):
    @output
    @render.ui
    def scale_note():
        return method_note(
            "Los niveles de intensidad (Bajo, Medio, Alto, Muy alto) se determinan mediante agrupamiento "
            "K-Means (k=4) ordenado estrictamente por la magnitud de sus centroides. "
            "El ranking clasifica los territorios de mayor a menor vulnerabilidad relativa "
            "según el escenario activo de ponderación.",
            title="Metodología de Clasificación y Jerarquía",
        )

    @output
    @render.ui
    def summary_cards():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        df = fd["municipios"] if vista == "Municipios" else fd["departamentos"]

        counts = df["riesgo_activo"].value_counts().to_dict()
        total_len = len(df)

        cards = []
        for level in INTENSIDAD_LEVELS:
            count = counts.get(level, 0)
            pct = (count / total_len * 100) if total_len > 0 else 0
            color = INTENSIDAD_PALETTE.get(level, "#315EEA")

            card = kpi_card(
                title=f"Nivel {level}",
                value=f"{count:,}".replace(",", "."),
                unit="territorios",
                subtitle=f"{pct:.1f}% del universo visible",
                indicator_color=color,
            )
            cards.append(card)

        return ui.tags.div(
            *cards,
            class_="atlas-kpi-grid",
            style="margin-bottom: 16px;",
        )

    @reactive.calc
    def processed_table():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")

        if vista == "Departamentos":
            df = fd["departamentos"].sort_values("score_activo", ascending=False).reset_index(drop=True)
            df["Ranking"] = range(1, len(df) + 1)
            display_df = df[
                ["Ranking", "cod_dpto", "dpto", "riesgo_activo", "score_activo", "municipios_total", "poblacion_total_depto"]
            ].rename(
                columns={
                    "cod_dpto": "DIVIPOLA",
                    "dpto": "Departamento",
                    "riesgo_activo": "Nivel de Riesgo",
                    "score_activo": "Índice Activo",
                    "municipios_total": "Municipios",
                    "poblacion_total_depto": "Población (DANE 2018)",
                }
            )
        else:
            df = fd["municipios"].sort_values("score_activo", ascending=False).reset_index(drop=True)
            df["Ranking"] = range(1, len(df) + 1)
            display_df = df[
                ["Ranking", "cod_mpio", "nom_mpio", "dpto", "riesgo_activo", "score_activo", "poblacion_total"]
            ].rename(
                columns={
                    "cod_mpio": "DIVIPOLA",
                    "nom_mpio": "Municipio",
                    "dpto": "Departamento",
                    "riesgo_activo": "Nivel de Riesgo",
                    "score_activo": "Índice Activo",
                    "poblacion_total": "Población (DANE 2018)",
                }
            )

        display_df["Índice Activo"] = display_df["Índice Activo"].round(2)
        display_df["Población (DANE 2018)"] = display_df["Población (DANE 2018)"].apply(
            lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "0"
        )
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

    @render.download_button(filename="ranking_atlas_territorial_laft.csv")
    def download_csv():
        buf = io.StringIO()
        processed_table().to_csv(buf, index=False, encoding="utf-8-sig")
        yield buf.getvalue()
