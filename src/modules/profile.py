"""
Módulo de Perfil Municipal con diagnóstico individual, gráficos interactivos
(radial y barras) y desglose multidimensional estandarizado.
Cumple con la estructura técnica definida en la Sección 10.
"""

from typing import Any, Dict
import pandas as pd
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_plotly

from src.components.cards import empty_state, kpi_card, method_note, risk_badge
from src.config import DIMENSIONES_TERRITORIALES, DIMENSION_LABELS
from src.visualizations.radar import (
    create_dimensions_bar_chart,
    create_radar_chart,
    empty_radar_figure,
)


@module.ui
def profile_ui():
    return ui.TagList(
        # 1 y 2. Identificación Territorial y Resumen Métrico
        ui.output_ui("resumen"),

        # 3 y 4. Comparación Gráfica frente a la Referencia Nacional (Radial + Barras)
        ui.layout_columns(
            ui.card(
                ui.card_header(
                    ui.h4(
                        "Perfil Multidimensional frente al Promedio Nacional",
                        style="font-size: 0.95rem; font-weight: 700; color: var(--atlas-blue-deep); margin: 0;",
                    ),
                ),
                ui.navset_pill(
                    ui.nav_panel("Perfil Radial (Spider)", output_widget("radar_chart")),
                    ui.nav_panel("Barras Comparativas", output_widget("bar_chart")),
                    id="profile_charts_nav",
                ),
                full_screen=True,
                min_height="480px",
            ),
            # 5. Desglose Detallado de Dimensiones
            ui.card(
                ui.card_header(
                    ui.div(
                        ui.h4(
                            "Desglose de Dimensiones Territoriales",
                            style="font-size: 0.95rem; font-weight: 700; color: var(--atlas-blue-deep); margin: 0;",
                        ),
                        ui.span(
                            "13 dimensiones normalizadas",
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
def profile_server(
    input,
    output,
    session,
    data: Dict[str, Any],
    filters_reactive: reactive.Calc,
    municipios_active_reactive: reactive.Calc,
):
    municipios_base = data["municipios"]

    @reactive.calc
    def selected_municipio():
        f = filters_reactive()
        cod = f.get("municipio", "")
        active_df = municipios_active_reactive()
        if cod:
            match = active_df[active_df["cod_mpio"] == cod]
            if not match.empty:
                return match.iloc[0]
            base_match = municipios_base[municipios_base["cod_mpio"] == cod]
            if not base_match.empty:
                return base_match.iloc[0]
        return active_df.iloc[0] if not active_df.empty else (municipios_base.iloc[0] if not municipios_base.empty else None)

    @output
    @render.ui
    def resumen():
        mun = selected_municipio()
        if mun is None:
            return empty_state(
                "Seleccione un municipio en el menú lateral para consultar su ficha técnica.",
                instruction="Use el selector de 'Municipio específico' en el panel de filtros.",
            )

        active_df = municipios_active_reactive().sort_values("score_activo", ascending=False).reset_index(drop=True)
        active_df["rank"] = range(1, len(active_df) + 1)
        rank_match = active_df[active_df["cod_mpio"] == mun["cod_mpio"]]
        rank_str = f"#{rank_match['rank'].iloc[0]}" if not rank_match.empty else "N/A"

        pob = f"{int(mun.get('poblacion_total', 0)):,}".replace(",", ".")
        tipo_mpio = str(mun.get("tipo_municipio", "Municipio"))
        nivel_riesgo = str(mun.get("riesgo_activo", mun.get("intensidad_territorial", "N/A")))
        score_val = float(mun.get("score_activo", mun.get("INDICE_TERRITORIAL", 0.0)))

        return ui.TagList(
            ui.tags.div(
                ui.tags.div(
                    ui.tags.span("FICHA MUNICIPAL • DIAGNÓSTICO INDIVIDUAL", style="font-size: 0.72rem; font-weight: 700; color: var(--atlas-blue-interactive); letter-spacing: 0.05em; margin-bottom: 2px;"),
                    ui.tags.h3(f"{mun['nom_mpio']} ({mun['dpto']})", style="font-size: 1.35rem; font-weight: 800; color: var(--atlas-blue-deep); margin: 0 0 4px 0;"),
                    ui.tags.p(
                        f"Código DIVIPOLA: {mun['cod_mpio']} • Tipo: {tipo_mpio} • Población: {pob} habs. (Censo DANE 2018)",
                        style="color: var(--atlas-text-secondary); font-size: 0.85rem; margin: 0;",
                    ),
                ),
                class_="atlas-territory-header",
            ),
            ui.tags.div(
                kpi_card(
                    title="Departamento",
                    value=str(mun["dpto"]),
                    subtitle="Jurisdicción departamental",
                ),
                kpi_card(
                    title="Nivel de Riesgo Activo",
                    value=nivel_riesgo,
                    subtitle="Clasificación K-Means",
                    indicator_color="#315EEA",
                ),
                kpi_card(
                    title="Índice Territorial",
                    value=f"{score_val:.2f}",
                    unit="pts",
                    subtitle="Puntuación relativa [0 - 100]",
                    indicator_color="#315EEA",
                ),
                kpi_card(
                    title="Posición en Ranking",
                    value=rank_str,
                    subtitle=f"De {len(active_df)} municipios evaluados",
                ),
                class_="atlas-kpi-grid",
                style="margin-bottom: 16px;",
            ),
        )

    @output
    @render_plotly
    def radar_chart():
        mun = selected_municipio()
        if mun is None:
            return empty_radar_figure("Seleccione un municipio para visualizar su comparativa")

        target_scores = {
            dim: float(mun.get(f"{dim}_SCORE", 0.0)) for dim in DIMENSIONES_TERRITORIALES
        }
        bench_scores = {
            dim: float(municipios_base[f"{dim}_SCORE"].mean())
            for dim in DIMENSIONES_TERRITORIALES
            if f"{dim}_SCORE" in municipios_base.columns
        }
        return create_radar_chart(
            target_scores=target_scores,
            target_name=str(mun["nom_mpio"]),
            benchmark_scores=bench_scores,
            benchmark_name="Promedio Nacional",
        )

    @output
    @render_plotly
    def bar_chart():
        mun = selected_municipio()
        if mun is None:
            return empty_radar_figure("Seleccione un municipio para visualizar su comparativa")

        target_scores = {
            dim: float(mun.get(f"{dim}_SCORE", 0.0)) for dim in DIMENSIONES_TERRITORIALES
        }
        bench_scores = {
            dim: float(municipios_base[f"{dim}_SCORE"].mean())
            for dim in DIMENSIONES_TERRITORIALES
            if f"{dim}_SCORE" in municipios_base.columns
        }
        return create_dimensions_bar_chart(
            target_scores=target_scores,
            target_name=str(mun["nom_mpio"]),
            benchmark_scores=bench_scores,
            benchmark_name="Promedio Nacional",
        )

    @output
    @render.ui
    def top_dimensions_callout():
        mun = selected_municipio()
        if mun is None:
            return ui.TagList()

        scores = [
            (dim, float(mun.get(f"{dim}_SCORE", 0.0))) for dim in DIMENSIONES_TERRITORIALES
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        top_3 = scores[:3]

        badges = [
            ui.tags.span(
                f"{DIMENSION_LABELS.get(d, d)}: {s:.1f} pts",
                style="font-size: 0.74rem; font-weight: 600; background: var(--atlas-surface-subtle); color: var(--atlas-blue-deep); padding: 3px 8px; border-radius: var(--atlas-radius-sm); border: 1px solid var(--atlas-border);",
            )
            for d, s in top_3
        ]

        return ui.tags.div(
            ui.tags.span("Dimensiones de mayor incidencia:", style="font-size: 0.76rem; font-weight: 700; color: var(--atlas-text-secondary); margin-right: 6px;"),
            *badges,
            style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; padding: 6px 10px; background: var(--atlas-bg-main); border-radius: var(--atlas-radius-sm);",
        )

    @output
    @render.data_frame
    def tabla_dimensiones():
        mun = selected_municipio()
        if mun is None:
            return render.DataGrid(pd.DataFrame(), selection_mode="none")

        rows = []
        for dim in DIMENSIONES_TERRITORIALES:
            score = float(mun.get(f"{dim}_SCORE", 0.0))
            intensidad = float(mun.get(f"{dim}_INTENSIDAD", 0.0))
            bench_val = float(municipios_base[f"{dim}_SCORE"].mean()) if f"{dim}_SCORE" in municipios_base.columns else 0.0
            rows.append(
                {
                    "Dimensión": DIMENSION_LABELS.get(dim, dim),
                    "Código": dim,
                    "Puntaje Municipio": round(score, 2),
                    "Promedio Nacional": round(bench_val, 2),
                    "Intensidad (Z-Score)": round(intensidad, 2),
                }
            )

        df_dim = pd.DataFrame(rows).sort_values("Puntaje Municipio", ascending=False)
        return render.DataGrid(df_dim, selection_mode="none", height="360px")
