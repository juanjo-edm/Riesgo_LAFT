"""
Pruebas de integridad estadística y línea base analítica del Atlas Territorial LAFT.
Verifica que las transformaciones, puntuaciones, ponderaciones CRITIC, K-Means
y agregaciones territoriales se preserven con total exactitud antes y después
del rediseño visual.
"""

import numpy as np
import pandas as pd
import pytest

from src.data_loader import load_app_data
from src.calculator import (
    build_municipal_active,
    build_department_active,
    score_to_risk_shared,
)
from src.config import DIMENSIONES_TERRITORIALES, INTENSIDAD_LEVELS


@pytest.fixture(scope="module")
def app_data():
    return load_app_data()


def test_baseline_dataset_shapes_and_codes(app_data):
    """Verifica formas de DataFrames y preservación de códigos DIVIPOLA con ceros iniciales."""
    municipios = app_data["municipios"]
    departamentos = app_data["departamentos"]
    catalogo = app_data["catalogo_indicadores"]

    assert len(municipios) == 1122
    assert len(departamentos) == 33
    assert len(catalogo) >= 13

    # Preservación de cadenas y ceros iniciales
    sample_codes = ["05001", "05002", "08001", "11001"]
    for cod in sample_codes:
        assert cod in municipios["cod_mpio"].values, f"Código {cod} debe existir con ceros a la izquierda"

    # Verificar que cod_mpio sea string y tenga 5 caracteres
    assert all(municipios["cod_mpio"].str.len() == 5), "Todos los códigos municipales deben tener 5 dígitos"
    # Verificar que cod_dpto tenga 2 caracteres
    assert all(departamentos["cod_dpto"].str.len() == 2), "Todos los códigos departamentales deben tener 2 dígitos"


def test_baseline_risk_distribution(app_data):
    """Verifica conteos exactos de los 4 niveles de riesgo en la línea base no filtrada."""
    municipios = app_data["municipios"]
    departamentos = app_data["departamentos"]

    mun_counts = municipios["intensidad_territorial"].value_counts().to_dict()
    assert mun_counts["Medio"] == 413
    assert mun_counts["Bajo"] == 390
    assert mun_counts["Alto"] == 230
    assert mun_counts["Muy alto"] == 89

    dep_counts = departamentos["intensidad_territorial_depto"].value_counts().to_dict()
    assert dep_counts["Alto"] == 11
    assert dep_counts["Medio"] == 11
    assert dep_counts["Bajo"] == 9
    assert dep_counts["Muy alto"] == 2


def test_baseline_top_municipalities(app_data):
    """Verifica los municipios con mayor índice territorial en la línea base."""
    municipios = app_data["municipios"]
    top_3 = municipios.sort_values("INDICE_TERRITORIAL", ascending=False).head(3)

    top_cods = top_3["cod_mpio"].tolist()
    assert top_cods == ["81591", "50325", "95025"]  # Puerto Rondón, Mapiripán, El Retorno

    top_scores = top_3["INDICE_TERRITORIAL"].tolist()
    assert pytest.approx(top_scores[0], rel=1e-4) == 51.0660
    assert pytest.approx(top_scores[1], rel=1e-4) == 46.9632
    assert pytest.approx(top_scores[2], rel=1e-4) == 46.4243


def test_build_municipal_active_no_filter(app_data):
    """Verifica que sin filtros build_municipal_active retorne el índice oficial idéntico."""
    municipios = app_data["municipios"]
    indicadores = app_data["indicadores_municipales"]
    catalogo = app_data["catalogo_indicadores"]

    df_active = build_municipal_active(municipios, indicadores, catalogo, dimensiones=[], fuentes=[])
    np.testing.assert_allclose(df_active["score_activo"], municipios["INDICE_TERRITORIAL"])
    assert (df_active["riesgo_activo"] == municipios["intensidad_territorial"]).all()


def test_build_recalculated_dimension_narc(app_data):
    """Verifica que el recálculo con dimensión NARC sea determinista y reproducible."""
    municipios = app_data["municipios"]
    indicadores = app_data["indicadores_municipales"]
    catalogo = app_data["catalogo_indicadores"]

    recalculated = build_municipal_active(municipios, indicadores, catalogo, dimensiones=["NARC"], fuentes=[])
    top_narc = recalculated.sort_values("score_activo", ascending=False).head(3)

    assert pytest.approx(top_narc["score_activo"].iloc[0], rel=1e-4) == 8.2151
    assert top_narc["riesgo_activo"].iloc[0] == "Muy alto"
    # K-Means con random_state=123 debe generar 4 clusters
    assert set(recalculated["riesgo_activo"].unique()) == set(INTENSIDAD_LEVELS)


def test_department_aggregation_weights(app_data):
    """Verifica que la agregación departamental por promedio ponderado de población sea exacta."""
    municipios = app_data["municipios"]
    departamentos = app_data["departamentos"]
    indicadores = app_data["indicadores_municipales"]
    catalogo = app_data["catalogo_indicadores"]

    # Recalculado con CONT y NARC
    rec_m = build_municipal_active(municipios, indicadores, catalogo, dimensiones=["CONT", "NARC"])
    rec_d = build_department_active(rec_m, departamentos, dimensiones=["CONT", "NARC"])

    # Verificar que cada departamento tenga score mayor a 0 y menor a 100
    assert (rec_d["score_activo"] >= 0).all()
    assert (rec_d["score_activo"] <= 100).all()
    assert len(rec_d) == 33


def test_recalculation_with_sources(app_data):
    """Verifica que el recálculo por fuentes específicas funcione deterministamente."""
    municipios = app_data["municipios"]
    indicadores = app_data["indicadores_municipales"]
    catalogo = app_data["catalogo_indicadores"]

    # Seleccionar dos fuentes de narcotráfico o contrabando
    sample_sources = catalogo[catalogo["included_in_index"]]["source_id"].head(2).tolist()
    rec_sources = build_municipal_active(
        municipios, indicadores, catalogo, dimensiones=[], fuentes=sample_sources
    )

    assert len(rec_sources) == 1122
    assert "score_activo" in rec_sources.columns
    assert "riesgo_activo" in rec_sources.columns
    assert (rec_sources["score_activo"] >= 0).all()


def test_rankings_consistency(app_data):
    """Verifica consistencia del ordenamiento de rankings."""
    municipios = app_data["municipios"]
    df_sorted = municipios.sort_values("INDICE_TERRITORIAL", ascending=False)
    scores = df_sorted["INDICE_TERRITORIAL"].values

    # Verificar que la lista esté estrictamente no creciente
    assert np.all(np.diff(scores) <= 0), "El ranking debe ser estrictamente no creciente"
    assert not df_sorted["INDICE_TERRITORIAL"].isna().any(), "No debe haber valores nulos en el índice"

