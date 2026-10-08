"""
Módulo de Perfil Departamental con agregación ponderada, gráfico de telaraña y desglose.
"""

from typing import Any, Dict
import numpy as np
import pandas as pd
from shiny import module, reactive, render, ui

from src.components.cards import empty_state, metric_card
from src.config import DIMENSIONES_TERRITORIALES, DIMENSION_LABELS
from src.visualizations.radar import create_radar_chart


@module.ui
def department_profile_ui():
    return ui.TagList(
        ui.output_ui("resumen"),
        ui.layout_columns(
            ui.tags.div(
                ui.tags.h5("Intensidad Departamental por Dimensión (Gráfico Radial)", style="font-weight: 700; color: #1e293b; margin-bottom: 12px;"),
                ui.output_ui("radar_chart"),
                style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);",
            ),
            ui.tags.div(
                ui.tags.h5("Dimensiones Ponderadas por Población", style="font-weight: 700; color: #1e293b; margin-bottom: 12px;"),
                ui.output_data_frame("tabla_dimensiones"),
                style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);",
            ),
            col_widths=[6, 6],
        ),
    )


@module.server
def department_profile_server(
    input,
    output,
    session,
    filters_reactive: reactive.Calc,
    departamentos_active_reactive: reactive.Calc,
    municipios_active_reactive: reactive.Calc,
):
    @reactive.calc
    def selected_department():
        f = filters_reactive()
        depto = f.get("departamento", "Todos")
        if not depto or depto == "Todos":
            return None

        active_df = departamentos_active_reactive()
        match = active_df[active_df["dpto"] == depto]
        return match.iloc[0] if not match.empty else None

    @reactive.calc
    def department_municipios():
        depto = selected_department()
        if depto is None:
            return pd.DataFrame()
        all_mun = municipios_active_reactive()
        return all_mun[all_mun["dpto"] == depto["dpto"]]

    @output
    @render.ui
    def resumen():
        depto = selected_department()
        if depto is None:
            return empty_state("Seleccione un departamento específico en el menú lateral para consultar su ficha técnica.")

        active_df = departamentos_active_reactive().sort_values("score_activo", ascending=False).reset_index(drop=True)
        active_df["rank"] = range(1, len(active_df) + 1)
        rank_match = active_df[active_df["dpto"] == depto["dpto"]]
        rank_str = f"#{rank_match['rank'].iloc[0]}" if not rank_match.empty else "N/A"

        pob = f"{int(depto.get('poblacion_total_depto', 0)):,}".replace(",", ".")

        return ui.TagList(
            ui.tags.div(
                ui.tags.h3(f"Departamento de {depto['dpto']}", style="font-weight: 800; color: #0f172a; margin-bottom: 4px;"),
                ui.tags.p(f"Código: {depto['cod_dpto']} | Población: {pob} habitantes | {depto['municipios_total']} Municipios", style="color: #64748b; font-size: 0.95rem; margin-bottom: 16px;"),
            ),
            ui.layout_columns(
                metric_card("Nivel de Intensidad", str(depto.get("riesgo_activo", "N/A"))),
                metric_card("Índice Departamental", f"{float(depto.get('score_activo', 0.0)):.2f}"),
                metric_card("Ranking Activo", rank_str, f"De {len(active_df)} departamentos"),
                metric_card("Total Municipios", str(depto.get("municipios_total", 0))),
                col_widths=[3, 3, 3, 3],
            ),
            ui.tags.div(style="margin-bottom: 18px;"),
        )

    @output
    @render.ui
    def radar_chart():
        depto = selected_department()
        muns = department_municipios()
        if depto is None or muns.empty:
            return None

        # Ponderación poblacional de los municipios del departamento
        weights = muns["poblacion_total"].clip(lower=1.0)
        target_scores = {}
        for dim in DIMENSIONES_TERRITORIALES:
            score_col = f"{dim}_SCORE"
            if score_col in muns.columns:
                target_scores[dim] = float(np.average(muns[score_col].fillna(0.0), weights=weights))
            else:
                target_scores[dim] = 0.0

        all_muns = municipios_active_reactive()
        bench_weights = all_muns["poblacion_total"].clip(lower=1.0)
        bench_scores = {}
        for dim in DIMENSIONES_TERRITORIALES:
            score_col = f"{dim}_SCORE"
            if score_col in all_muns.columns:
                bench_scores[dim] = float(np.average(all_muns[score_col].fillna(0.0), weights=bench_weights))
            else:
                bench_scores[dim] = 0.0

        fig = create_radar_chart(
            target_scores=target_scores,
            target_name=f"Dpto. {depto['dpto']}",
            benchmark_scores=bench_scores,
            benchmark_name="Promedio Nacional",
        )
        return ui.HTML(fig.to_html(include_plotlyjs="cdn", full_html=False))

    @output
    @render.data_frame
    def tabla_dimensiones():
        depto = selected_department()
        muns = department_municipios()
        if depto is None or muns.empty:
            return render.DataGrid(pd.DataFrame(), selection_mode="none")

        weights = muns["poblacion_total"].clip(lower=1.0)
        rows = []
        for dim in DIMENSIONES_TERRITORIALES:
            score_col = f"{dim}_SCORE"
            val = float(np.average(muns[score_col].fillna(0.0), weights=weights)) if score_col in muns.columns else 0.0
            rows.append(
                {
                    "Dimensión": DIMENSION_LABELS.get(dim, dim),
                    "Código": dim,
                    "Puntaje Ponderado": round(val, 2),
                }
            )

        df_dim = pd.DataFrame(rows).sort_values("Puntaje Ponderado", ascending=False)
        return render.DataGrid(df_dim, selection_mode="none", height="420px")
