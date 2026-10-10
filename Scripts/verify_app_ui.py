"""
Script de verificación visual y funcional con Playwright.
Ejecuta la aplicación en un servidor local, navega por las 4 vistas principales,
valida interactividad y captura pantallas en escritorio (1440x900) y móvil (390x844).
"""

import subprocess
import sys
import time
from pathlib import Path
import requests
from playwright.sync_api import Page, expect, sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "Output" / "playwright" / "territorial_filters"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8055
APP_URL = f"http://127.0.0.1:{PORT}"

# Instrumentación exclusiva de pruebas: permite consultar el viewport real de
# Leaflet y disparar sus eventos, sin exponer objetos internos en la aplicación.
MAP_INSPECTOR = """
    let leaflet;
    Object.defineProperty(window, 'L', {
        configurable: true,
        get: () => leaflet,
        set: api => {
            leaflet = api;
            if (api && api.Map) api.Map.addInitHook(function() {
                this.getContainer().__testMap = this;
            });
        }
    });
    window.testMap = () => document.querySelector('#map-territory_map .leaflet-container')?.__testMap;
    window.testTerritory = code => Object.values(testMap()?._layers || {}).find(layer =>
        layer.feature && String(layer.feature.properties.cod_mpio || layer.feature.properties.cod_dpto) === code);
"""


def wait_for_server(url: str, timeout: int = 30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f"[OK] Servidor respondiendo en {url}")
                return True
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"El servidor no respondió en {url} dentro de {timeout} segundos.")


def search_territory(page: Page, input_id: str, query: str, value: str):
    page.wait_for_function("([id, value]) => document.getElementById(id).selectize.options[value]", arg=[input_id, value])
    search = page.locator(f"#{input_id}-selectized")
    search.click()
    search.fill(query)
    option = page.locator(
        f"#{input_id} + .selectize-control .selectize-dropdown .option[data-value='{value}']"
    )
    expect(option).to_be_visible()
    option.click()
    expect(page.locator(f"#{input_id}")).to_have_value(value)


def map_viewport(page: Page):
    return page.evaluate("() => ({center: testMap().getCenter(), zoom: testMap().getZoom()})")


def wait_for_focus(page: Page, code: str):
    page.wait_for_function("code => { const layer = testTerritory(code); return layer && layer.options.color === '#315EEA'; }", arg=code)
    page.wait_for_function("() => !document.documentElement.classList.contains('shiny-busy')")
    page.wait_for_function("""code => {
        const map = testMap(), bounds = testTerritory(code).getBounds();
        const sw = bounds.getSouthWest(), ne = bounds.getNorthEast();
        const dx = (ne.lng - sw.lng) * .1, dy = (ne.lat - sw.lat) * .1;
        const padded = L.latLngBounds([sw.lat - dy, sw.lng - dx], [ne.lat + dy, ne.lng + dx]);
        return map.getBounds().contains(padded) && map.getZoom() === map.getBoundsZoom(padded);
    }""", arg=code)


def verify_map_focus(page: Page, label: str):
    page.wait_for_function("() => window.L && testMap() && testTerritory('11001')")
    page.wait_for_function("() => Math.abs(testMap().getCenter().lng + 74.29205) < .1")
    initial = map_viewport(page)
    map_id = page.locator("#map-territory_map .leaflet-container").evaluate("el => el._leaflet_id")
    expect(page.locator("#filters-municipio")).to_have_value("11001")
    expect(page.locator("#map-selected_territory_drawer")).to_be_empty()
    assert page.evaluate("() => Object.values(testMap()._layers).filter(l => l.feature).every(l => l.options.fillOpacity === .76)")

    # Elegir explícitamente Bogotá, aunque ya sea el valor inicial del selector.
    search_territory(page, "filters-municipio", "bogota", "11001")
    wait_for_focus(page, "11001")
    expect(page.locator("#map-floating_info_box")).to_contain_text("Selección fijada")
    assert page.evaluate("() => Object.values(testMap()._layers).filter(l => l.feature).every(l => l.options.fillOpacity === (l === testTerritory('11001') ? .88 : 0))")
    assert map_viewport(page)["zoom"] > initial["zoom"]
    page.locator("#map-territory_map").screenshot(path=str(OUTPUT_DIR / f"{label}_mapa_bogota_enfocada.png"))

    # Hover real sobre un vecino: sin cambiar su relleno, la selección ni el zoom.
    viewport = map_viewport(page)
    page.evaluate("() => testTerritory('25754')._path.dataset.testNeighbor = 'true'")
    neighbor = page.locator("path[data-test-neighbor='true']")
    neighbor_box = neighbor.bounding_box()
    neighbor.dispatch_event("mouseover", {"clientX": neighbor_box["x"] + neighbor_box["width"] / 2, "clientY": neighbor_box["y"] + neighbor_box["height"] / 2})
    expect(page.locator("#map-floating_info_box")).to_contain_text("SOACHA")
    assert float(neighbor.get_attribute("fill-opacity")) == 0
    assert map_viewport(page) == viewport
    neighbor.dispatch_event("mouseout")

    # Un clic en ese vecino actualiza el selector y limpia la información previa.
    neighbor.dispatch_event("click")
    expect(page.locator("#filters-municipio")).to_have_value("25754")
    wait_for_focus(page, "25754")
    expect(page.locator("#map-selected_territory_drawer h3")).to_have_text("SOACHA")

    # Cambiar únicamente indicadores conserva el zoom manual y el widget.
    manual_zoom = map_viewport(page)["zoom"] + 1
    page.locator("#map-territory_map .leaflet-control-zoom-in").click()
    page.wait_for_function("zoom => testMap().getZoom() === zoom && !testMap()._animatingZoom", arg=manual_zoom)
    page.wait_for_function("() => !document.documentElement.classList.contains('shiny-busy')")
    manual = map_viewport(page)
    page.locator("details:has(#filters-dimensiones) summary").click()
    page.locator("#filters-dimensiones input[value='NARC']").check()
    expect(page.locator("#filters-scenario_status")).to_contain_text("Personalizado")
    page.wait_for_function("() => !document.documentElement.classList.contains('shiny-busy')")
    assert map_viewport(page)["zoom"] == manual["zoom"], (manual, map_viewport(page))
    assert page.evaluate("center => testMap().latLngToContainerPoint(center).distanceTo(testMap().getSize().divideBy(2)) < 1", manual["center"])
    assert page.locator("#map-territory_map .leaflet-container").evaluate("el => el._leaflet_id") == map_id

    # Selecciones consecutivas: el último territorio determina el encuadre.
    search_territory(page, "filters-municipio", "medellin", "05001")
    search_territory(page, "filters-municipio", "cali", "76001")
    wait_for_focus(page, "76001")
    expect(page.locator("#map-floating_info_box")).to_contain_text("SANTIAGO DE CALI")

    # Departamento específico cambia automáticamente el nivel y enfoca su límite.
    search_territory(page, "filters-departamento", "antio", "ANTIOQUIA")
    expect(page.locator("#filters-vista")).to_have_value("Departamentos")
    wait_for_focus(page, "05")
    page.locator("#map-territory_map").screenshot(path=str(OUTPUT_DIR / f"{label}_mapa_antioquia_enfocada.png"))

    page.locator("#filters-vista").select_option("Municipios")
    expect(page.locator("#map-selected_territory_drawer")).to_be_empty()
    search_territory(page, "filters-municipio", "envigado", "05266")
    wait_for_focus(page, "05266")

    # Excluir su nivel de riesgo elimina el enfoque, no lo recupera al reactivar.
    risk = page.evaluate("() => testTerritory('05266').feature.properties.riesgo_activo")
    page.locator("details:has(#filters-niveles) summary").click()
    page.locator(f"#filters-niveles input[value='{risk}']").uncheck()
    expect(page.locator("#map-selected_territory_drawer")).to_be_empty()
    page.locator(f"#filters-niveles input[value='{risk}']").check()
    page.wait_for_function("() => testTerritory('05266')")
    expect(page.locator("#map-selected_territory_drawer")).to_be_empty()

    search_territory(page, "filters-departamento", "todos", "Todos")
    expect(page.locator("#map-selected_territory_drawer")).to_be_empty()
    search_territory(page, "filters-municipio", "nuevo belen", "27493")
    expect(page.locator("#map-focus_notice")).to_contain_text("no tiene geometría disponible")
    assert page.evaluate("() => Object.values(testMap()._layers).filter(l => l.feature).every(l => l.options.fillOpacity === .76)")
    page.screenshot(path=str(OUTPUT_DIR / f"{label}_mapa_sin_geometria.png"))

    page.locator("#filters-clear_filters").click()
    expect(page.locator("#map-focus_notice")).to_be_empty()
    expect(page.locator("#map-selected_territory_drawer")).to_be_empty()
    expect(page.locator("#filters-municipio")).to_have_value("11001")
    expect(page.locator("#filters-departamento")).to_have_value("Todos")
    page.wait_for_function("""initial => {
        const center = testMap().getCenter(); return testMap().getZoom() === initial.zoom &&
        testMap().latLngToContainerPoint(initial.center).distanceTo(testMap().getSize().divideBy(2)) < 1;
    }""", arg=initial)
    page.locator("#map-territory_map").screenshot(path=str(OUTPUT_DIR / f"{label}_mapa_nacional_restablecido.png"))

    # También el clic departamental sincroniza el selector correspondiente.
    page.locator("#filters-vista").select_option("Departamentos")
    page.wait_for_function("() => testTerritory('05')")
    page.evaluate("() => testTerritory('05')._path.dataset.testDepartment = 'true'")
    page.locator("path[data-test-department='true']").dispatch_event("click")
    expect(page.locator("#filters-departamento")).to_have_value("ANTIOQUIA")
    wait_for_focus(page, "05")
    page.locator("#filters-clear_filters").click()
    expect(page.locator("#filters-municipio")).to_have_value("11001")
    expect(page.locator("#map-selected_territory_drawer")).to_be_empty()

    search = page.locator("#filters-municipio-selectized")
    search.click()
    search.fill("bogota")
    expect(page.locator("#filters-municipio + .selectize-control .option[data-value='11001']")).to_be_visible()
    search.press("Enter")
    wait_for_focus(page, "11001")
    page.locator("#filters-clear_filters").click()
    expect(page.locator("#map-selected_territory_drawer")).to_be_empty()
    print(f"  [OK] Enfoque, hover, clic, zoom manual, exclusión y geometría ausente ({label})")


def verify_territorial_filters(page: Page, label: str, mobile: bool = False):
    expect(page.locator("#filters-municipio-selectized")).to_be_visible()
    search_territory(page, "filters-municipio", "medellin", "05001")
    expect(page.locator("#profile-resumen h3")).to_have_text("MEDELLÍN (ANTIOQUIA)")

    # Conservar un municipio que pertenece al departamento seleccionado.
    search_territory(page, "filters-departamento", "antio", "ANTIOQUIA")
    expect(page.locator("#filters-municipio")).to_have_value("05001")
    page.wait_for_function(
        "() => Object.values(document.getElementById('filters-municipio').selectize.options)"
        ".filter(option => option.value).every(option => option.label.endsWith('(ANTIOQUIA)'))"
    )
    expect(page.locator("#filters-vista")).to_have_value("Departamentos")
    page.locator("#filters-vista").select_option("Municipios")

    search_territory(page, "filters-municipio", "envigado", "05266")
    expect(page.locator("#profile-resumen h3")).to_have_text("ENVIGADO (ANTIOQUIA)")

    # Una consulta sin coincidencias no crea ni cambia territorios.
    search = page.locator("#filters-municipio-selectized")
    search.click()
    search.fill("municipio inexistente")
    expect(page.locator("#filters-municipio + .selectize-control .option:visible")).to_have_count(0)
    search.press("Escape")
    expect(page.locator("#filters-municipio")).to_have_value("05266")

    # Resultados acotados y altura táctil en pantallas pequeñas.
    search.click()
    search.fill("")
    options = page.locator("#filters-municipio + .selectize-control .option:visible")
    expect(options.first).to_be_visible()
    assert 0 < options.count() <= 50
    if mobile:
        assert options.first.bounding_box()["height"] >= 44
        assert page.locator("#filters-municipio + .selectize-control .selectize-input").bounding_box()["height"] >= 44
    page.screenshot(path=str(OUTPUT_DIR / f"{label}_municipios_busqueda.png"))
    search.press("Escape")

    # Restablecer desde una lista limitada debe recuperar Bogotá y todo el catálogo.
    page.locator("#filters-clear_filters").click()
    expect(page.locator("#filters-departamento")).to_have_value("Todos")
    expect(page.locator("#filters-municipio")).to_have_value("11001")
    expect(page.locator("#profile-resumen h3")).to_have_text("BOGOTÁ, D.C. (BOGOTÁ, D.C.)")
    search_territory(page, "filters-municipio", "cali", "76001")
    expect(page.locator("#profile-resumen h3")).to_have_text("SANTIAGO DE CALI (VALLE DEL CAUCA)")
    page.locator("#filters-clear_filters").click()
    expect(page.locator("#filters-municipio")).to_have_value("11001")

    print(f"  [OK] Búsqueda, jerarquía territorial y restablecimiento ({label})")


def verify_radar(page: Page, output_id: str, label: str):
    plot = page.locator(f"#{output_id} .js-plotly-plot")
    expect(plot).to_be_visible()
    page.wait_for_function(
        "id => { const plot = document.querySelector('#' + id + ' .js-plotly-plot'); "
        "return plot && plot._fullLayout && plot.data.length === 2; }",
        arg=output_id,
    )
    assert plot.evaluate("plot => plot._fullLayout.polar.radialaxis.range") == [0, 12]
    assert plot.evaluate("plot => plot._fullLayout.polar.radialaxis.dtick") == 3
    expect(plot.locator(".angularaxistick text")).to_have_count(13)
    assert plot.evaluate(
        "plot => { const bounds = plot.getBoundingClientRect(); "
        "return Array.from(plot.querySelectorAll('.angularaxistick text')).every(label => { "
        "const box = label.getBoundingClientRect(); return box.left >= bounds.left "
        "&& box.right <= bounds.right && box.top >= bounds.top && box.bottom <= bounds.bottom; }); }"
    ), "Las etiquetas del radar deben quedar dentro del gráfico"
    plot.screenshot(path=str(OUTPUT_DIR / f"{label}_radar.png"))
    print(f"  [OK] Radar 0–12 con dos series ({label})")


def main():
    print(f"[INFO] Iniciando servidor Shiny en puerto {PORT}...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "shiny", "run", "app.py", "--port", str(PORT)],
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        wait_for_server(APP_URL, timeout=25)

        with sync_playwright() as p:
            print("[INFO] Lanzando navegador Chromium...")
            browser = p.chromium.launch(headless=True)

            # -------------------------------------------------------------
            # 1. Desktop Suite (1440 x 900)
            # -------------------------------------------------------------
            print("[INFO] Ejecutando pruebas en escritorio (1440x900)...")
            context_desktop = browser.new_context(viewport={"width": 1440, "height": 900})
            context_desktop.add_init_script(MAP_INSPECTOR)
            page = context_desktop.new_page()

            # Capturar logs de consola
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda error: console_errors.append(str(error)))

            page.goto(APP_URL, wait_until="networkidle")
            page.wait_for_timeout(3500)  # Esperar estabilización de ipyleaflet y websockets
            verify_map_focus(page, "desktop")

            # Vista 1: Mapa Territorial (Desktop)
            page.screenshot(path=str(OUTPUT_DIR / "01_mapa_desktop_1440x900.png"), full_page=False)
            print("  [OK] Capturado: 01_mapa_desktop_1440x900.png")

            # Abrir modal de metodología
            btn_metodologia = page.locator("button:has-text('Metodología Quarto')")
            if btn_metodologia.count() > 0:
                btn_metodologia.click()
                page.wait_for_timeout(800)
                page.screenshot(path=str(OUTPUT_DIR / "05_modal_metodologia_desktop.png"))
                print("  [OK] Capturado: 05_modal_metodologia_desktop.png")
                # Cerrar modal
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)

            # Vista 2: Rankings
            tab_rankings = page.locator(".nav-link:has-text('Rankings')")
            tab_rankings.click()
            page.wait_for_timeout(2500)
            page.screenshot(path=str(OUTPUT_DIR / "02_rankings_desktop_1440x900.png"), full_page=False)
            print("  [OK] Capturado: 02_rankings_desktop_1440x900.png")

            # Vista 3: Perfil Municipal
            tab_perfil = page.locator(".nav-link:has-text('Perfil Municipal')")
            tab_perfil.click()
            page.wait_for_timeout(4000)
            verify_radar(page, "profile-radar_chart", "desktop_municipal")
            verify_territorial_filters(page, "desktop")
            page.screenshot(path=str(OUTPUT_DIR / "03_perfil_municipal_desktop_1440x900.png"), full_page=False)
            print("  [OK] Capturado: 03_perfil_municipal_desktop_1440x900.png")

            # Probar cambio a pestaña de barras comparativas en perfil
            tab_barras = page.locator("#profile_charts_nav .nav-link:has-text('Barras Comparativas'), .nav-link:has-text('Barras Comparativas')").first
            if tab_barras.count() > 0:
                tab_barras.click()
                page.wait_for_timeout(3500)
                page.screenshot(path=str(OUTPUT_DIR / "03b_perfil_municipal_barras_desktop.png"), full_page=False)
                print("  [OK] Capturado: 03b_perfil_municipal_barras_desktop.png")

            # Vista 4: Perfil Departamental
            tab_depto = page.locator(".nav-link:has-text('Perfil Departamental')")
            tab_depto.click()
            page.wait_for_timeout(3500)
            verify_radar(page, "department_profile-radar_chart", "desktop_departamental")
            page.screenshot(path=str(OUTPUT_DIR / "04_perfil_departamental_desktop_1440x900.png"), full_page=False)
            print("  [OK] Capturado: 04_perfil_departamental_desktop_1440x900.png")

            context_desktop.close()

            # -------------------------------------------------------------
            # 2. Mobile Suite (390 x 844 - iPhone 14/15/16)
            # -------------------------------------------------------------
            print("[INFO] Ejecutando pruebas en móvil (390x844)...")
            context_mobile = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                is_mobile=True,
                has_touch=True,
            )
            context_mobile.add_init_script(MAP_INSPECTOR)
            page_m = context_mobile.new_page()
            page_m.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page_m.on("pageerror", lambda error: console_errors.append(str(error)))
            page_m.goto(APP_URL, wait_until="networkidle")
            page_m.wait_for_timeout(3500)
            verify_map_focus(page_m, "mobile")

            # Vista 1: Mapa (Mobile)
            page_m.screenshot(path=str(OUTPUT_DIR / "06_mapa_mobile_390x844.png"), full_page=False)
            print("  [OK] Capturado: 06_mapa_mobile_390x844.png")

            # Vista 2: Rankings (Mobile)
            page_m.locator(".nav-link:has-text('Rankings')").click()
            page_m.wait_for_timeout(1800)
            page_m.screenshot(path=str(OUTPUT_DIR / "07_rankings_mobile_390x844.png"), full_page=False)
            print("  [OK] Capturado: 07_rankings_mobile_390x844.png")

            # Vista 3: Perfil Municipal (Mobile)
            page_m.locator(".nav-link:has-text('Perfil Municipal')").click()
            page_m.wait_for_timeout(2000)
            verify_radar(page_m, "profile-radar_chart", "mobile_municipal")
            verify_territorial_filters(page_m, "mobile", mobile=True)
            page_m.screenshot(path=str(OUTPUT_DIR / "08_perfil_municipal_mobile_390x844.png"), full_page=False)
            print("  [OK] Capturado: 08_perfil_municipal_mobile_390x844.png")

            # Vista 4: Perfil Departamental (Mobile)
            page_m.locator(".nav-link:has-text('Perfil Departamental')").click()
            page_m.wait_for_timeout(2000)
            verify_radar(page_m, "department_profile-radar_chart", "mobile_departamental")
            page_m.screenshot(path=str(OUTPUT_DIR / "09_perfil_departamental_mobile_390x844.png"), full_page=False)
            print("  [OK] Capturado: 09_perfil_departamental_mobile_390x844.png")

            context_mobile.close()
            browser.close()

            print(f"[EXITO] Todas las capturas se generaron correctamente en {OUTPUT_DIR}")
            if console_errors:
                print(f"[ADVERTENCIA] Errores detectados en consola del navegador: {len(console_errors)}")
                for err in console_errors[:5]:
                    print("   -", err)
            else:
                print("[OK] Cero errores críticos de consola en el navegador.")
            assert not console_errors, console_errors

    finally:
        print("[INFO] Deteniendo servidor de prueba...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
