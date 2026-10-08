"""
Componentes de interfaz reutilizables para Shiny: tarjetas de métricas, badges y avisos.
"""

from shiny import ui
from src.config import INTENSIDAD_PALETTE


def risk_badge(level: str) -> ui.Tag:
    """Renderiza un badge de nivel de riesgo con su color respectivo."""
    bg_color = INTENSIDAD_PALETTE.get(level, "#64748b")
    text_color = "#0f172a" if level in ["Medio", "Bajo"] else "#ffffff"

    return ui.tags.span(
        level,
        style=f"""
            display: inline-block;
            background-color: {bg_color};
            color: {text_color};
            font-weight: 600;
            font-size: 0.85rem;
            padding: 3px 10px;
            border-radius: 9999px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        """,
    )


def metric_card(title: str, value: str, subtitle: str | None = None, border_color: str = "#28246f") -> ui.Tag:
    """Renderiza una tarjeta de resumen métrico estilizada."""
    children = [
        ui.tags.span(title, style="display: block; color: #64748b; font-size: 0.82rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;"),
        ui.tags.strong(value, style="display: block; color: #0f172a; font-size: 1.4rem; font-weight: 700; margin-top: 2px;"),
    ]
    if subtitle:
        children.append(ui.tags.small(subtitle, style="display: block; color: #94a3b8; font-size: 0.78rem; margin-top: 2px;"))

    return ui.tags.div(
        *children,
        style=f"""
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid {border_color};
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        """,
    )


def empty_state(message: str) -> ui.Tag:
    """Mensaje para estados sin selección o sin datos."""
    return ui.tags.div(
        ui.tags.p(message, style="margin: 0; font-size: 0.95rem; color: #64748b;"),
        style="""
            background: #f8fafc;
            border: 1px dashed #cbd5e1;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            margin: 16px 0;
        """,
    )


def method_note(text: str) -> ui.Tag:
    """Caja informativa para notas metodológicas."""
    return ui.tags.div(
        ui.tags.div("💡 Nota metodológica", style="font-weight: 700; color: #28246f; margin-bottom: 4px; font-size: 0.85rem;"),
        ui.tags.div(text, style="font-size: 0.88rem; color: #334155; line-height: 1.4;"),
        style="""
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #28246f;
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 14px;
        """,
    )
