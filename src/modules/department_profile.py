"""
Módulo de Perfil Departamental con agregación ponderada por población censal,
gráficos interactivos (radar y barras comparativas) y desglose multidimensional.
Cumple con la estructura de análisis y visualización de la Sección 10.
"""

from typing import Any, Dict
import numpy as np
import pandas as pd
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_plotly

from src.components.cards import empty_state, kpi_card, risk_badge
from src.config import DIMENSIONES_TERRITORIALES, DIMENSION_LABELS
from src.visualizations.radar import (
    create_dimensions_bar_chart,
    create_radar_chart,
    empty_radar_figure,
)


@module.ui
def department_profile_ui():
    return ui.TagList(
        # 1 y 2. Identificación Territorial Departamental y Resumen Métrico
        ui.output_ui("resumen"),

        # 3 y 4. Comparación Gráfica frente a la Referencia Nacional (Radial + Barras)
        ui.layout_columns(
            ui.card(
                ui.card_header(
                    ui.h4(
                        "Perfil Departamental frente al Promedio Nacional",
                        style="font-size: 0.95rem; font-weight: 700; color: var(--atlas-blue-deep); margin: 0;",
                    ),
                ),
                ui.navset_pill(
                    ui.nav_panel("Perfil Radial (Spider)", output_widget("radar_chart")),
                    ui.nav_panel("Barras Comparativas", output_widget("bar_chart")),
                    id="dept_charts_nav",
                ),
                full_screen=True,
                min_height="480px",
            ),
            # 5. Desglose Detallado de Dimensiones Ponderadas
            ui.card(
                ui.card_header(
                    ui.div(
                        ui.h4(
                            "Dimensiones Ponderadas por Población",
                            style="font-size: 0.95rem; font-weight: 700; color: var(--atlas-blue-deep); margin: 0;",
                        ),
                        ui.span(
                            "Ponderación censal DANE 2018",
                            style="font-size: 0.74rem; color: var(--atlas-text-muted);",
                        ),
                        class_="d-flex justify-content-between align-items-center w-100",
                    ),
                ),
                ui.output_ui("top_dimensions_callout"),
                ui.output_data_frame("tabla_dimensiones"),
                full_screen=True,
                min_height="480px",
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
        active_df = departamentos_active_reactive()
        if depto and depto != "Todos":
            match = active_df[active_df["dpto"] == depto]
            if not match.empty:
                return match.iloc[0]
        return active_df.iloc[0] if not active_df.empty else None

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
            return empty_state(
                "Seleccione un departamento específico en el menú lateral para consultar su ficha técnica.",
                instruction="Use el selector de 'Departamento' en el panel de filtros.",
            )

        active_df = departamentos_active_reactive().sort_values("score_activo", ascending=False).reset_index(drop=True)
        active_df["rank"] = range(1, len(active_df) + 1)
        rank_match = active_df[active_df["dpto"] == depto["dpto"]]
        rank_str = f"#{rank_match['rank'].iloc[0]}" if not rank_match.empty else "N/A"

        pob = f"{int(depto.get('poblacion_total_depto', 0)):,}".replace(",", ".")
        score_val = float(depto.get("score_activo", 0.0))
        nivel_riesgo = str(depto.get("riesgo_activo", "N/A"))

        return ui.TagList(
            ui.tags.div(
                ui.tags.div(
                    ui.tags.span("FICHA DEPARTAMENTAL • AGREGACIÓN PONDERADA", style="font-size: 0.72rem; font-weight: 700; color: var(--atlas-blue-interactive); letter-spacing: 0.05em; margin-bottom: 2px;"),
                    ui.tags.h3(f"Departamento de {depto['dpto']}", style="font-size: 1.35rem; font-weight: 800; color: var(--atlas-blue-deep); margin: 0 0 4px 0;"),
                    ui.tags.p(
                        f"Código DIVIPOLA: {depto['cod_dpto']} • Población Departamental: {pob} habs. (Censo DANE 2018) • {depto['municipios_total']} Municipios",
                        style="color: var(--atlas-text-secondary); font-size: 0.85rem; margin: 0;",
                    ),
                ),
                class_="atlas-territory-header",
            ),
            ui.tags.div(
                kpi_card(
                    title="Nivel de Riesgo Departamental",
                    value=nivel_riesgo,
                    subtitle="Clasificación relativa K-Means",
                    indicator_color="#315EEA",
                ),
                kpi_card(
                    title="Índice Departamental Ponderado",
                    value=f"{score_val:.2f}",
                    unit="pts",
                    subtitle="Promedio ponderado por población",
                    indicator_color="#315EEA",
                ),
                kpi_card(
                    title="Posición en Ranking",
                    value=rank_str,
                    subtitle=f"De {len(active_df)} departamentos",
                ),
                kpi_card(
                    title="Municipios Evaluados",
                    value=str(depto.get("municipios_total", 0)),
                    unit="mpios",
                    subtitle="Cobertura territorial completa",
                ),
                class_="atlas-kpi-grid",
                style="margin-bottom: 16px;",
            ),
        )

    @output
    @render_plotly
    def radar_chart():
        depto = selected_department()
        muns = department_municipios()
        if depto is None or muns.empty:
            return empty_radar_figure("Seleccione un departamento para visualizar su comparativa")

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

        return create_radar_chart(
            target_scores=target_scores,
            target_name=f"Dpto. {depto['dpto']}",
            benchmark_scores=bench_scores,
            benchmark_name="Promedio Nacional",
        )

    @output
    @render_plotly
    def bar_chart():
        depto = selected_department()
        muns = department_municipios()
        if depto is None or muns.empty:
            return empty_radar_figure("Seleccione un departamento para visualizar su comparativa")

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

        return create_dimensions_bar_chart(
            target_scores=target_scores,
            target_name=f"Dpto. {depto['dpto']}",
            benchmark_scores=bench_scores,
            benchmark_name="Promedio Nacional Ponderado",
        )

    @output
    @render.ui
    def top_dimensions_callout():
        depto = selected_department()
        muns = department_municipios()
        if depto is None or muns.empty:
            return ui.TagList()

        weights = muns["poblacion_total"].clip(lower=1.0)
        dim_scores = []
        for dim in DIMENSIONES_TERRITORIALES:
            score_col = f"{dim}_SCORE"
            val = float(np.average(muns[score_col].fillna(0.0), weights=weights)) if score_col in muns.columns else 0.0
            dim_scores.append((dim, val))

        dim_scores.sort(key=lambda x: x[1], reverse=True)
        top_3 = dim_scores[:3]

        badges = [
            ui.tags.span(
                f"{DIMENSION_LABELS.get(d, d)}: {s:.1f} pts",
                style="font-size: 0.74rem; font-weight: 600; background: var(--atlas-surface-subtle); color: var(--atlas-blue-deep); padding: 3px 8px; border-radius: var(--atlas-radius-sm); border: 1px solid var(--atlas-border);",
            )
            for d, s in top_3
        ]

        return ui.tags.div(
            ui.tags.span("Dimensiones departamentales destacadas:", style="font-size: 0.76rem; font-weight: 700; color: var(--atlas-text-secondary); margin-right: 6px;"),
            *badges,
            style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; padding: 6px 10px; background: var(--atlas-bg-main); border-radius: var(--atlas-radius-sm);",
        )

    @output
    @render.data_frame
    def tabla_dimensiones():
        depto = selected_department()
        muns = department_municipios()
        if depto is None or muns.empty:
            return render.DataGrid(pd.DataFrame(), selection_mode="none")

        all_muns = municipios_active_reactive()
        bench_weights = all_muns["poblacion_total"].clip(lower=1.0)
        weights = muns["poblacion_total"].clip(lower=1.0)

        rows = []
        for dim in DIMENSIONES_TERRITORIALES:
            score_col = f"{dim}_SCORE"
            val = float(np.average(muns[score_col].fillna(0.0), weights=weights)) if score_col in muns.columns else 0.0
            bench_val = float(np.average(all_muns[score_col].fillna(0.0), weights=bench_weights)) if score_col in all_muns.columns else 0.0
            rows.append(
                {
                    "Dimensión": DIMENSION_LABELS.get(dim, dim),
                    "Código": dim,
                    "Puntaje Departamental": round(val, 2),
                    "Referencia Nacional": round(bench_val, 2),
                }
            )

        df_dim = pd.DataFrame(rows).sort_values("Puntaje Departamental", ascending=False)
        return render.DataGrid(df_dim, selection_mode="none", height="360px")
