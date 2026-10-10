"""
Módulo de Mapa Interactivo con ipyleaflet y componentes modernos para Shiny for Python.
Implementa el rediseño de explorador geográfico (Sección 7) y tarjetas KPI (Sección 8).
"""

from typing import Any, Callable, Dict, Optional
import pandas as pd
from shiny import module, reactive, render, ui
from shinywidgets import output_widget, reactive_read, render_widget

from src.components.cards import kpi_card, risk_badge
from src.config import INTENSIDAD_PALETTE
from src.visualizations.map_builder import (
    build_ipyleaflet_map,
    frame_map,
    format_feature_info_html,
    format_initial_info_box,
    update_ipyleaflet_map,
    viewport_has_arrived,
)


@module.ui
def map_ui():
    return ui.TagList(
        # Fila superior de tarjetas KPI (Sección 8)
        ui.output_ui("metrics_summary"),

        # Tarjeta del Explorador Cartográfico (Sección 7)
        ui.card(
            ui.card_header(
                ui.div(
                    ui.div(
                        ui.h4(
                            "Distribución Geográfica del Riesgo Territorial",
                            style="font-size: 0.98rem; font-weight: 700; color: var(--atlas-blue-deep); margin: 0;",
                        ),
                        ui.p(
                            "Seleccione por clic o filtros • Consulte vecinos con el cursor",
                            style="font-size: 0.78rem; color: var(--atlas-text-secondary); margin: 2px 0 0 0;",
                        ),
                    ),
                    ui.span(
                        "Cartografía Territorial • WGS84",
                        style="font-size: 0.74rem; font-weight: 600; color: var(--atlas-text-muted); background: var(--atlas-surface-subtle); padding: 4px 8px; border-radius: var(--atlas-radius-sm); border: 1px solid var(--atlas-border);",
                    ),
                    class_="d-flex justify-content-between align-items-center w-100 flex-wrap gap-2",
                ),
            ),
            ui.output_ui("focus_notice"),
            ui.div(
                output_widget("territory_map", width="100%", height="580px"),
                ui.output_ui("floating_info_box"),
                class_="atlas-map-wrapper",
            ),
            full_screen=True,
            fill=False,
        ),

        # Script de activación y cálculo de dimensiones para Leaflet en navegadores y webviews
        ui.tags.script(
            """
            (function() {
                function wakeMap() {
                    window.dispatchEvent(new Event('resize'));
                    try {
                        if (window.parent && window.parent !== window) {
                            window.parent.dispatchEvent(new Event('resize'));
                        }
                    } catch(e) {}
                }
                setTimeout(wakeMap, 100);
                setTimeout(wakeMap, 350);
                setTimeout(wakeMap, 800);
                setTimeout(wakeMap, 1500);
                document.addEventListener('shown.bs.tab', wakeMap);
                window.addEventListener('focus', wakeMap);
            })();
            """
        ),

        # Ficha contextual del territorio actualmente seleccionado
        ui.output_ui("selected_territory_drawer"),
    )


@module.server
def map_server(
    input,
    output,
    session,
    filtered_data: reactive.Calc,
    geodata: Dict[str, Any],
    selected_territory: Optional[reactive.Calc] = None,
    selection_revision: Optional[reactive.Value] = None,
    on_select_callback: Optional[Callable] = None,
):
    @output
    @render.ui
    def metrics_summary():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        df = fd["municipios"] if vista == "Municipios" else fd["departamentos"]

        if df.empty:
            return ui.tags.div(
                ui.tags.p("No hay territorios que coincidan con los filtros seleccionados.", style="margin: 0; font-weight: 500;"),
                class_="alert alert-warning",
                style="border-radius: var(--atlas-radius-md); font-size: 0.88rem;",
            )

        total_territorios = f"{len(df):,}".replace(",", ".")
        score_promedio = f"{df['score_activo'].mean():.2f}"
        modo_riesgo = df["riesgo_activo"].mode()[0] if not df["riesgo_activo"].empty else "N/A"
        badge_dot_color = INTENSIDAD_PALETTE.get(modo_riesgo, "#315EEA")

        pob_col = "poblacion_total" if vista == "Municipios" else "poblacion_total_depto"
        pob_total = df[pob_col].sum() if pob_col in df.columns else 0
        pob_str = f"{pob_total:,.0f}".replace(",", ".")

        return ui.tags.div(
            kpi_card(
                title="Territorios Visibles",
                value=total_territorios,
                unit="municipios" if vista == "Municipios" else "departamentos",
                subtitle=f"Ámbito territorial activo ({vista})",
            ),
            kpi_card(
                title="Índice Activo Promedio",
                value=score_promedio,
                unit="pts",
                subtitle="Escala relativa [0 - 100]",
                indicator_color="#315EEA",
            ),
            kpi_card(
                title="Intensidad Predominante",
                value=modo_riesgo,
                subtitle="Mayoría en el universo visible",
                indicator_color=badge_dot_color,
            ),
            kpi_card(
                title="Población Cubierta",
                value=pob_str,
                unit="hab.",
                subtitle="Referencia Censo DANE 2018",
            ),
            class_="atlas-kpi-grid",
        )

    hovered_territory = reactive.Value(None)
    territory_widget = build_ipyleaflet_map(
        geodata=None,
        data=pd.DataFrame(),
        join_key="cod_mpio",
        on_hover_callback=hovered_territory.set,
        on_select_callback=on_select_callback,
    )
    previous_frame = [None]
    frame_request = reactive.Value(None)
    applied_frame = [None]
    pending_viewport = [None]

    @reactive.effect
    def _update_map():
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        municipal = vista == "Municipios"
        df = fd["municipios" if municipal else "departamentos"]
        geo = geodata.get("mapa_municipios" if municipal else "mapa_departamentos")
        key = "cod_mpio" if municipal else "cod_dpto"
        st = selected_territory() if selected_territory is not None else None
        code = str(st[key]) if st else None
        revision = selection_revision.get() if selection_revision is not None else 0
        frame = (vista, code, revision, fd.get("map_scope"))
        hovered_territory.set(None)
        bounds = update_ipyleaflet_map(
            territory_widget, geo, df, key, vista,
            selected_code=code, fit_view=False,
        )
        if frame != previous_frame[0]:
            frame_request.set({"key": frame, "bounds": bounds})
        previous_frame[0] = frame

    @reactive.effect
    def _frame_map():
        request = frame_request.get()
        reactive_read(territory_widget, "pixel_bounds")
        reactive_read(territory_widget, "bounds")
        if request and request["key"] != applied_frame[0]:
            if frame_map(territory_widget, request["bounds"]):
                applied_frame[0] = request["key"]
                pending_viewport[0] = (tuple(territory_widget.center), territory_widget.zoom)
        if pending_viewport[0] and viewport_has_arrived(territory_widget, *pending_viewport[0]):
            hovered_territory.set(None)
            pending_viewport[0] = None

    @output
    @render.ui
    def focus_notice():
        st = selected_territory() if selected_territory is not None else None
        if not st:
            return ui.TagList()
        vista = filtered_data()["vista"]
        municipal = vista == "Municipios"
        key = "cod_mpio" if municipal else "cod_dpto"
        geo = geodata.get("mapa_municipios" if municipal else "mapa_departamentos")
        match = geo[geo[key].astype(str) == str(st[key])] if geo is not None else None
        if match is None or match.empty or not (match.geometry.notna() & ~match.geometry.is_empty).any():
            name = st.get("nom_mpio" if municipal else "dpto", "El territorio")
            return ui.div(
                f"{name} no tiene geometría disponible. Se conserva la vista general del universo filtrado.",
                class_="alert alert-warning mb-0", role="status",
            )
        return ui.TagList()

    @output
    @render.ui
    def floating_info_box():
        p = hovered_territory()
        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        join_key = "cod_mpio" if vista == "Municipios" else "cod_dpto"
        score_col = "score_activo"
        risk_col = "riesgo_activo"

        if not p:
            st = selected_territory() if selected_territory is not None else None
            if st:
                return ui.HTML(
                    f'<div class="atlas-floating-infobox">'
                    f'{format_feature_info_html(st, join_key, vista, score_col, risk_col, is_pinned=True)}'
                    f'</div>'
                )
            return ui.HTML(
                f'<div class="atlas-floating-infobox">'
                f'{format_initial_info_box()}'
                f'</div>'
            )

        return ui.HTML(
            f'<div class="atlas-floating-infobox">'
            f'{format_feature_info_html(p, join_key, vista, score_col, risk_col, is_pinned=False)}'
            f'</div>'
        )

    @output
    @render_widget
    def territory_map():
        return territory_widget

    @output
    @render.ui
    def selected_territory_drawer():
        if selected_territory is None:
            return ui.TagList()

        st = selected_territory()
        if not st:
            return ui.TagList()

        fd = filtered_data()
        vista = fd.get("vista", "Municipios")
        df = fd["municipios"] if vista == "Municipios" else fd["departamentos"]

        cod_col = "cod_mpio" if vista == "Municipios" else "cod_dpto"
        code = str(st.get(cod_col, ""))
        nombre = st.get("nom_mpio" if vista == "Municipios" else "dpto", "Territorio")
        depto = st.get("dpto", "")

        match = df[df[cod_col] == code]
        if match.empty:
            return ui.TagList()

        row = match.iloc[0]
        score = float(row.get("score_activo", 0.0))
        riesgo = str(row.get("riesgo_activo", "N/A"))

        # Ranking en el universo activo
        sorted_df = df.sort_values("score_activo", ascending=False).reset_index(drop=True)
        sorted_df["rank"] = range(1, len(sorted_df) + 1)
        r_match = sorted_df[sorted_df[cod_col] == code]
        rank_pos = r_match["rank"].iloc[0] if not r_match.empty else "N/A"

        pob_col = "poblacion_total" if vista == "Municipios" else "poblacion_total_depto"
        pob_val = row.get(pob_col, 0)
        pob_str = f"{int(pob_val):,}".replace(",", ".")

        depto_meta = f"Departamento de {depto} • " if vista == "Municipios" and depto else ""

        return ui.tags.div(
            ui.tags.div(
                ui.tags.div(
                    ui.tags.div("FICHA TERRITORIAL SELECCIONADA", style="font-size: 0.72rem; font-weight: 700; color: var(--atlas-blue-interactive); letter-spacing: 0.05em; margin-bottom: 2px;"),
                    ui.tags.h3(nombre, style="font-size: 1.15rem; font-weight: 800; color: var(--atlas-blue-deep); margin: 0;"),
                    ui.tags.p(f"{depto_meta}DIVIPOLA: {code} | Censo DANE 2018: {pob_str} habitantes", style="font-size: 0.78rem; color: var(--atlas-text-secondary); margin: 2px 0 0 0;"),
                ),
                ui.tags.div(
                    ui.tags.div(
                        ui.tags.span("Índice Activo:", style="font-size: 0.75rem; color: var(--atlas-text-muted); display: block;"),
                        ui.tags.strong(f"{score:.2f}", style="font-size: 1.25rem; color: var(--atlas-text-main); font-family: var(--atlas-font-display);"),
                        style="text-align: right;",
                    ),
                    risk_badge(riesgo),
                    ui.tags.div(
                        ui.tags.span("Ranking:", style="font-size: 0.75rem; color: var(--atlas-text-muted); display: block;"),
                        ui.tags.strong(f"#{rank_pos} de {len(df)}", style="font-size: 0.88rem; color: var(--atlas-text-main); font-weight: 700;"),
                        style="text-align: right;",
                    ),
                    style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;",
                ),
                class_="d-flex justify-content-between align-items-center w-100 flex-wrap gap-3",
            ),
            class_="atlas-territory-card",
            style="margin-top: 14px;",
        )
