"""
Visualizaciones interactivas con Plotly para perfiles territoriales:
- Gráfico radial / telaraña (radar chart)
- Gráfico de barras horizontales comparativo frente al promedio nacional
"""

from textwrap import wrap
from typing import Dict, Optional
import plotly.graph_objects as go

from src.config import DIMENSIONES_TERRITORIALES, DIMENSION_LABELS


def create_radar_chart(
    target_scores: Dict[str, float],
    target_name: str,
    benchmark_scores: Optional[Dict[str, float]] = None,
    benchmark_name: str = "Promedio Nacional",
) -> go.Figure:
    """
    Crea un gráfico de telaraña (radar chart) interactivo con Plotly comparando
    las 13 dimensiones del territorio seleccionado frente al promedio nacional.
    """
    categories = [DIMENSION_LABELS.get(d, d) for d in DIMENSIONES_TERRITORIALES]
    values_target = [float(target_scores.get(d, 0.0)) for d in DIMENSIONES_TERRITORIALES]

    # Cerrar el polígono repitiendo el primer vértice
    r_target = values_target + [values_target[0]]
    theta_categories = categories + [categories[0]]

    fig = go.Figure()

    # Traza del Benchmark Nacional (línea punteada neutra)
    if benchmark_scores is not None:
        values_bench = [float(benchmark_scores.get(d, 0.0)) for d in DIMENSIONES_TERRITORIALES]
        r_bench = values_bench + [values_bench[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=r_bench,
                theta=theta_categories,
                fill="toself",
                name=benchmark_name,
                line=dict(color="#64748B", dash="dash", width=1.5),
                fillcolor="rgba(148, 163, 184, 0.15)",
                hovertemplate="<b>%{theta}</b><br>Promedio: %{r:.2f} pts<extra></extra>",
            )
        )

    # Traza del Territorio Seleccionado (línea destacada azul profundo / interacción)
    fig.add_trace(
        go.Scatterpolar(
            r=r_target,
            theta=theta_categories,
            fill="toself",
            name=target_name,
            line=dict(color="#315EEA", width=2.4),
            fillcolor="rgba(49, 94, 234, 0.22)",
            hovertemplate="<b>%{theta}</b><br>" + target_name + ": %{r:.2f} pts<extra></extra>",
        )
    )

    font_family = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 12],
                tick0=0,
                dtick=3,
                tickfont=dict(size=9.5, color="#64748B", family=font_family),
                gridcolor="#E2E8F0",
                linecolor="#CBD5E1",
            ),
            angularaxis=dict(
                tickmode="array",
                tickvals=categories,
                ticktext=["<br>".join(wrap(label, width=14)) for label in categories],
                tickfont=dict(size=10, color="#17253B", family=font_family),
                direction="clockwise",
                gridcolor="#E2E8F0",
                linecolor="#CBD5E1",
            ),
            bgcolor="rgba(248, 250, 252, 0.7)",
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.20,
            xanchor="center",
            x=0.5,
            font=dict(size=11.5, color="#334155", family=font_family),
        ),
        margin=dict(l=65, r=65, t=55, b=65),
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def create_dimensions_bar_chart(
    target_scores: Dict[str, float],
    target_name: str,
    benchmark_scores: Optional[Dict[str, float]] = None,
    benchmark_name: str = "Promedio Nacional",
) -> go.Figure:
    """
    Crea un gráfico de barras horizontales comparativo para facilitar la lectura
    directa y ordenada de las dimensiones de riesgo frente al promedio nacional.
    """
    rows = []
    for d in DIMENSIONES_TERRITORIALES:
        t_val = float(target_scores.get(d, 0.0))
        b_val = float(benchmark_scores.get(d, 0.0)) if benchmark_scores else 0.0
        label = DIMENSION_LABELS.get(d, d)
        rows.append({"dim": d, "label": label, "target": t_val, "bench": b_val})

    # Ordenar por puntaje del territorio de mayor a menor (para barras horizontales se invierte al graficar)
    rows.sort(key=lambda x: x["target"], reverse=False)

    labels = [r["label"] for r in rows]
    targets = [r["target"] for r in rows]
    benches = [r["bench"] for r in rows]

    fig = go.Figure()

    # Barras de referencia nacional
    fig.add_trace(
        go.Bar(
            y=labels,
            x=benches,
            name=benchmark_name,
            orientation="h",
            marker=dict(color="#CBD5E1", line=dict(color="#94A3B8", width=1)),
            hovertemplate="<b>%{y}</b><br>" + benchmark_name + ": %{x:.2f} pts<extra></extra>",
        )
    )

    # Barras del territorio seleccionado
    fig.add_trace(
        go.Bar(
            y=labels,
            x=targets,
            name=target_name,
            orientation="h",
            marker=dict(color="#315EEA", line=dict(color="#14243A", width=1)),
            hovertemplate="<b>%{y}</b><br>" + target_name + ": %{x:.2f} pts<extra></extra>",
        )
    )

    font_family = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

    fig.update_layout(
        barmode="group",
        bargroupgap=0.15,
        xaxis=dict(
            title=dict(
                text="Puntuación de Riesgo [0 - 100]",
                font=dict(size=11, color="#64748B", family=font_family),
            ),
            tickfont=dict(size=10, color="#64748B", family=font_family),
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
        ),
        yaxis=dict(
            tickfont=dict(size=10.5, color="#17253B", family=font_family),
            gridcolor="rgba(0,0,0,0)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#334155", family=font_family),
        ),
        margin=dict(l=10, r=20, t=30, b=35),
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def empty_radar_figure(message: str = "Seleccione un territorio para visualizar su perfil") -> go.Figure:
    """Retorna un Figure de Plotly con estado vacío elegante."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=13, color="#64748B", family="Inter, -apple-system, sans-serif"),
    )
    fig.update_layout(
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=430,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig
