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


def metric_card(title: str, value: str, subtitle: str | None = None, border_color: str = "#312e81") -> ui.Tag:
    """Renderiza una tarjeta de resumen métrico estilizada con diseño moderno."""
    children = [
        ui.tags.span(
            title,
            style="display: block; color: #64748b; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 2px;",
        ),
        ui.tags.strong(
            value,
            style="display: block; color: #0f172a; font-size: 1.45rem; font-weight: 800; line-height: 1.2;",
        ),
    ]
    if subtitle:
        children.append(
            ui.tags.small(
                subtitle,
                style="display: block; color: #94a3b8; font-size: 0.78rem; margin-top: 4px; font-weight: 500;",
            )
        )

    return ui.tags.div(
        *children,
        style=f"""
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid {border_color};
            border-radius: 10px;
            padding: 14px 18px;
            box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        """,
    )


def empty_state(message: str) -> ui.Tag:
    """Mensaje para estados sin selección o sin datos."""
    return ui.tags.div(
        ui.tags.p(message, style="margin: 0; font-size: 0.95rem; color: #64748b; font-weight: 500; max-width: 450px; margin: 0 auto;"),
        style="""
            background: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 32px 20px;
            text-align: center;
            margin: 16px 0;
        """,
    )


def method_note(text: str) -> ui.Tag:
    """Caja informativa para notas metodológicas."""
    return ui.tags.div(
        ui.tags.div("Nota metodológica", style="font-weight: 700; color: #312e81; margin-bottom: 4px; font-size: 0.85rem; letter-spacing: 0.3px;"),
        ui.tags.div(text, style="font-size: 0.88rem; color: #334155; line-height: 1.5;"),
        style="""
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #4338ca;
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        """,
    )
