"""
Gráficos interactivos de telaraña (radar chart) con Plotly.
"""

from typing import Dict, List, Sequence
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.config import DIMENSIONES_TERRITORIALES, DIMENSION_LABELS


def create_radar_chart(
    target_scores: Dict[str, float],
    target_name: str,
    benchmark_scores: Dict[str, float] | None = None,
    benchmark_name: str = "Promedio Nacional",
) -> go.Figure:
    """
    Crea un gráfico de telaraña (radar chart) interactivo con Plotly comparando
    las dimensiones del territorio seleccionado frente al promedio nacional.
    """
    categories = [DIMENSION_LABELS.get(d, d) for d in DIMENSIONES_TERRITORIALES]
    values_target = [float(target_scores.get(d, 0.0)) for d in DIMENSIONES_TERRITORIALES]

    # Cerrar el polígono repitiendo el primer elemento
    r_target = values_target + [values_target[0]]
    theta_categories = categories + [categories[0]]

    fig = go.Figure()

    # Benchmark (Promedio Nacional) si está presente
    if benchmark_scores is not None:
        values_bench = [float(benchmark_scores.get(d, 0.0)) for d in DIMENSIONES_TERRITORIALES]
        r_bench = values_bench + [values_bench[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=r_bench,
                theta=theta_categories,
                fill="toself",
                name=benchmark_name,
                line=dict(color="rgba(100, 116, 139, 0.7)", dash="dash", width=1.5),
                fillcolor="rgba(148, 163, 184, 0.15)",
                hoverinfo="theta+r+name",
            )
        )

    # Territorio seleccionado
    fig.add_trace(
        go.Scatterpolar(
            r=r_target,
            theta=theta_categories,
            fill="toself",
            name=target_name,
            line=dict(color="#28246f", width=2.5),
            fillcolor="rgba(40, 36, 111, 0.35)",
            hoverinfo="theta+r+name",
        )
    )

    max_val = max(max(values_target, default=10), 10)
    radial_range_max = max(100, int(np.ceil(max_val / 10.0) * 10))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, radial_range_max],
                tickfont=dict(size=10, color="#64748b", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"),
                gridcolor="#e2e8f0",
                linecolor="#cbd5e1",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#0f172a", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"),
                direction="clockwise",
                gridcolor="#e2e8f0",
                linecolor="#cbd5e1",
            ),
            bgcolor="rgba(248, 250, 252, 0.6)",
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#334155", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"),
        ),
        margin=dict(l=45, r=45, t=35, b=45),
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def empty_radar_figure(message: str = "Seleccione un territorio para visualizar su perfil radial") -> go.Figure:
    """
    Retorna un Figure de Plotly con estado vacío elegante para inicialización segura en shinywidgets.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#64748b", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"),
    )
    fig.update_layout(
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig
