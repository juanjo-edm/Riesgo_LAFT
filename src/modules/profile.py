"""
Módulo de Perfil Municipal con gráfico de telaraña Plotly y desglose de dimensiones.
"""

from typing import Any, Dict
import pandas as pd
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, render_plotly

from src.components.cards import empty_state, metric_card
from src.config import DIMENSIONES_TERRITORIALES, DIMENSION_LABELS, DIMENSION_SCORE_COLS
from src.visualizations.radar import create_radar_chart, empty_radar_figure


@module.ui
def profile_ui():
    return ui.TagList(
        ui.output_ui("resumen"),
        ui.layout_columns(
            ui.card(
                ui.card_header(
                    ui.span("Intensidad por Dimensión (Perfil Radial)", style="font-weight: 700; color: #1e1b4b; font-size: 0.95rem;"),
                ),
                output_widget("radar_chart"),
                full_screen=True,
            ),
            ui.card(
                ui.card_header(
                    ui.span("Desglose Detallado de Dimensiones", style="font-weight: 700; color: #1e1b4b; font-size: 0.95rem;"),
                ),
                ui.output_data_frame("tabla_dimensiones"),
                full_screen=True,
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
            return empty_state("Seleccione un municipio en el menú lateral para consultar su ficha técnica.")

        active_df = municipios_active_reactive().sort_values("score_activo", ascending=False).reset_index(drop=True)
        active_df["rank"] = range(1, len(active_df) + 1)
        rank_match = active_df[active_df["cod_mpio"] == mun["cod_mpio"]]
        rank_str = f"#{rank_match['rank'].iloc[0]}" if not rank_match.empty else "N/A"

        pob = f"{int(mun.get('poblacion_total', 0)):,}".replace(",", ".")

        return ui.TagList(
            ui.tags.div(
                ui.tags.h3(f"{mun['nom_mpio']} ({mun['dpto']})", style="font-weight: 800; color: #0f172a; margin-bottom: 4px;"),
                ui.tags.p(f"Código Divipola: {mun['cod_mpio']} | Población: {pob} habitantes", style="color: #64748b; font-size: 0.95rem; margin-bottom: 16px;"),
            ),
            ui.layout_columns(
                metric_card("Departamento", str(mun["dpto"])),
                metric_card("Nivel de Riesgo", str(mun.get("riesgo_activo", mun.get("intensidad_territorial", "N/A")))),
                metric_card("Índice Territorial", f"{float(mun.get('score_activo', mun.get('INDICE_TERRITORIAL', 0.0))):.2f}"),
                metric_card("Ranking Activo", rank_str, f"De {len(active_df)} municipios"),
                col_widths=[3, 3, 3, 3],
            ),
            ui.tags.div(style="margin-bottom: 18px;"),
        )

    @output
    @render_plotly
    def radar_chart():
        mun = selected_municipio()
        if mun is None:
            return empty_radar_figure("Seleccione un municipio en el menú lateral para ver su perfil radial")

        # Scores del municipio
        target_scores = {
            dim: float(mun.get(f"{dim}_SCORE", 0.0)) for dim in DIMENSIONES_TERRITORIALES
        }

        # Promedio nacional de referencia
        bench_scores = {
            dim: float(municipios_base[f"{dim}_SCORE"].mean())
            for dim in DIMENSIONES_TERRITORIALES
            if f"{dim}_SCORE" in municipios_base.columns
        }

        fig = create_radar_chart(
            target_scores=target_scores,
            target_name=str(mun["nom_mpio"]),
            benchmark_scores=bench_scores,
            benchmark_name="Promedio Nacional",
        )
        return fig

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
            rows.append(
                {
                    "Dimensión": DIMENSION_LABELS.get(dim, dim),
                    "Código": dim,
                    "Puntaje": round(score, 2),
                    "Intensidad (Z-score)": round(intensidad, 2),
                }
            )

        df_dim = pd.DataFrame(rows).sort_values("Puntaje", ascending=False)
        return render.DataGrid(df_dim, selection_mode="none", height="420px")
