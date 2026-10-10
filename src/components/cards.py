"""
Componentes de interfaz reutilizables para Shiny: tarjetas KPI, badges, notas y estados vacíos.
Diseño orientado a Geospatial Intelligence y accesibilidad WCAG 2.2 AA.
"""

from typing import Optional
from shiny import ui
from src.config import INTENSIDAD_PALETTE


def risk_badge(level: str, count: Optional[int] = None) -> ui.Tag:
    """
    Renderiza un badge discreto de nivel de riesgo con su dot semántico y alto contraste.
    """
    level_class_map = {
        "Bajo": "bajo",
        "Medio": "medio",
        "Alto": "alto",
        "Muy alto": "muy-alto",
    }
    css_class = level_class_map.get(level, "bajo")
    count_str = f" ({count:,})".replace(",", ".") if count is not None else ""

    return ui.tags.span(
        ui.tags.span(class_="atlas-risk-dot"),
        ui.tags.span(f"{level}{count_str}"),
        class_=f"atlas-risk-badge {css_class}",
    )


def kpi_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    unit: Optional[str] = None,
    indicator_color: Optional[str] = None,
) -> ui.Tag:
    """
    Renderiza una tarjeta KPI con superficie neutra, tipografía protagonista y contexto conciso.
    Cumple con las directrices de diseño analítico (Sección 8).
    """
    indicator_style = f"background-color: {indicator_color};" if indicator_color else ""

    header_children = [ui.tags.span(title, class_="atlas-kpi-title")]
    if indicator_color:
        header_children.append(ui.tags.span(class_="atlas-kpi-indicator", style=indicator_style))

    value_children = [ui.tags.span(value, class_="atlas-kpi-value")]
    if unit:
        value_children.append(ui.tags.span(unit, class_="atlas-kpi-unit"))

    body_children = [
        ui.tags.div(*header_children, class_="atlas-kpi-header"),
        ui.tags.div(*value_children, class_="atlas-kpi-value-row"),
    ]

    if subtitle:
        body_children.append(ui.tags.p(subtitle, class_="atlas-kpi-subtitle"))

    return ui.tags.div(*body_children, class_="atlas-kpi-card")


def metric_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    border_color: str = "#315EEA",
) -> ui.Tag:
    """
    Tarjeta de resumen métrico con borde de acento interactivo para fichas de perfil.
    """
    children = [
        ui.tags.span(title, class_="atlas-kpi-title"),
        ui.tags.div(
            ui.tags.span(value, class_="atlas-kpi-value"),
            class_="atlas-kpi-value-row",
        ),
    ]
    if subtitle:
        children.append(ui.tags.p(subtitle, class_="atlas-kpi-subtitle"))

    return ui.tags.div(
        *children,
        class_="atlas-kpi-card",
        style=f"border-left: 3px solid {border_color};",
    )


def empty_state(message: str, instruction: Optional[str] = None) -> ui.Tag:
    """Renderiza un estado vacío instructivo y accesible."""
    children = [
        ui.tags.div("🗺️", class_="atlas-empty-state-icon"),
        ui.tags.p(message, class_="atlas-empty-state-text"),
    ]
    if instruction:
        children.append(
            ui.tags.small(instruction, style="display: block; margin-top: 6px; color: var(--atlas-text-muted);")
        )

    return ui.tags.div(*children, class_="atlas-empty-state")


def method_note(text: str, title: str = "Nota metodológica") -> ui.Tag:
    """Caja informativa limpia para notas de referencia técnica o metodológica."""
    return ui.tags.div(
        ui.tags.div(title, class_="atlas-method-card-title"),
        ui.tags.p(text, class_="atlas-method-card-text"),
        class_="atlas-method-card",
    )


def scenario_badge(
    recalculated: bool,
    label: str,
    active_count: int = 0,
) -> ui.Tag:
    """
    Muestra el estado del índice: General (oficial) vs Recalculado (personalizado con CRITIC).
    """
    if recalculated:
        return ui.tags.div(
            ui.tags.div(
                ui.tags.span("⚡", style="font-size: 0.85rem;"),
                ui.tags.span("Escenario Personalizado (CRITIC)"),
                class_="atlas-scenario-title",
                style="color: #92400E;",
            ),
            ui.tags.p(
                f"{label} • {active_count} factor(es) activo(s) con reclasificación K-Means dinámica.",
                class_="atlas-scenario-desc",
            ),
            class_="atlas-scenario-card recalculated",
        )
    else:
        return ui.tags.div(
            ui.tags.div(
                ui.tags.span("🏛️", style="font-size: 0.85rem;"),
                ui.tags.span("Índice Territorial General"),
                class_="atlas-scenario-title",
                style="color: var(--atlas-blue-interactive);",
            ),
            ui.tags.p(
                "Ponderación multivariada global consolidada sobre las 13 dimensiones de riesgo.",
                class_="atlas-scenario-desc",
            ),
            class_="atlas-scenario-card general",
        )
