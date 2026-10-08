"""
Motor de cálculo reactivo para scores territoriales y clasificación K-Means.
"""

from typing import List, Sequence, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.config import (
    DIMENSIONES_TERRITORIALES,
    DIMENSION_LABELS,
    INTENSIDAD_LEVELS,
)


def score_values_to_level(values: Sequence[float]) -> List[str]:
    """
    Clasifica un vector de scores numéricos en 4 niveles de intensidad
    ('Bajo', 'Medio', 'Alto', 'Muy alto') mediante K-Means ordenado por centroides.
    """
    arr = np.array(values, dtype=float)
    valid_mask = np.isfinite(arr)
    valid_vals = arr[valid_mask]

    n_unique = len(np.unique(valid_vals))
    result = [None] * len(arr)

    if n_unique == 0:
        return ["Bajo"] * len(arr)

    k = min(4, n_unique)
    if k == 1:
        return ["Bajo"] * len(arr)

    km = KMeans(n_clusters=k, n_init=50, max_iter=100, random_state=123)
    km.fit(valid_vals.reshape(-1, 1))

    # Ordenar los centroides de menor a mayor
    centers = km.cluster_centers_.flatten()
    sorted_cluster_indices = np.argsort(centers)
    # cluster_id -> intensidad_level
    cluster_to_level = {
        sorted_cluster_indices[i]: INTENSIDAD_LEVELS[i] for i in range(k)
    }

    labels = [cluster_to_level[c] for c in km.labels_]
    idx_valid = 0
    for i, is_valid in enumerate(valid_mask):
        if is_valid:
            result[i] = labels[idx_valid]
            idx_valid += 1
        else:
            result[i] = "Bajo"

    return result


def score_to_risk_shared(
    municipios: pd.DataFrame, departamentos: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clasifica conjuntamente municipios y departamentos sobre la misma escala de clusters.
    """
    mun_scores = municipios["score_activo"].values
    dep_scores = departamentos["score_activo"].values
    combined = np.concatenate([mun_scores, dep_scores])

    combined_levels = score_values_to_level(combined)
    n_mun = len(mun_scores)

    mun_copy = municipios.copy()
    dep_copy = departamentos.copy()

    mun_copy["riesgo_activo"] = combined_levels[:n_mun]
    mun_copy["intensidad_activa"] = mun_copy["riesgo_activo"]

    dep_copy["riesgo_activo"] = combined_levels[n_mun:]
    dep_copy["intensidad_activa"] = dep_copy["riesgo_activo"]

    return mun_copy, dep_copy


def get_score_label(
    dimensiones: List[str] | None = None,
    fuentes: List[str] | None = None,
    catalogo: pd.DataFrame | None = None,
) -> str:
    """Genera la etiqueta descriptiva del índice activo."""
    if not dimensiones and not fuentes:
        return "Índice territorial global"

    if fuentes and catalogo is not None:
        source_labels = catalogo[catalogo["source_id"].isin(fuentes)]["source_label"].tolist()
        if len(source_labels) == 1:
            return f"Indicador: {source_labels[0]}"
        elif len(source_labels) <= 3:
            return f"Indicadores: {', '.join(source_labels)}"
        else:
            return f"Índice focalizado ({len(source_labels)} fuentes)"

    if dimensiones:
        labels = [DIMENSION_LABELS.get(d, d) for d in dimensiones]
        if len(labels) == 1:
            return f"Dimensión: {labels[0]}"
        else:
            return f"Dimensiones seleccionadas ({len(labels)})"

    return "Índice personalizado"


def build_municipal_active(
    municipios: pd.DataFrame,
    indicadores: pd.DataFrame,
    catalogo: pd.DataFrame,
    dimensiones: List[str] | None = None,
    fuentes: List[str] | None = None,
    assign_level: bool = True,
) -> pd.DataFrame:
    """
    Calcula el score activo municipal según las dimensiones y fuentes seleccionadas.
    """
    df = municipios.copy()
    dimensiones = [d for d in (dimensiones or []) if d in DIMENSIONES_TERRITORIALES]
    all_valid_sources = set(catalogo[catalogo["included_in_index"]]["source_id"])
    fuentes = [f for f in (fuentes or []) if f in all_valid_sources]

    # Caso 1: Sin filtros (Índice oficial total)
    if not dimensiones and not fuentes:
        df["score_activo"] = df["INDICE_TERRITORIAL"]
        df["intensidad_activa"] = df["intensidad_territorial"].fillna("Bajo")
        df["riesgo_activo"] = df["intensidad_activa"]
        df["score_label"] = get_score_label()
        df["indicadores_activos"] = len(all_valid_sources)
        return df

    # Caso 2: Fuentes específicas seleccionadas
    if fuentes:
        cat_filtrado = catalogo[catalogo["included_in_index"]]
        if dimensiones:
            cat_filtrado = cat_filtrado[cat_filtrado["dimension_id"].isin(dimensiones)]
        fuentes_activas = cat_filtrado[cat_filtrado["source_id"].isin(fuentes)]["source_id"].tolist()

        ind_filtrados = indicadores[indicadores["source_id"].isin(fuentes_activas)]
        resumen = (
            ind_filtrados.groupby("cod_mpio")
            .agg(
                score_activo=("source_score", "mean"),
                indicadores_activos=("source_id", "nunique"),
            )
            .reset_index()
        )

        df = df.merge(resumen, on="cod_mpio", how="left")
        df["score_activo"] = df["score_activo"].fillna(0.0)
        df["indicadores_activos"] = df["indicadores_activos"].fillna(0).astype(int)
        df["score_label"] = get_score_label(dimensiones, fuentes_activas, catalogo)

    # Caso 3: Dimensiones completas seleccionadas
    else:
        score_cols = [f"{dim}_SCORE" for dim in dimensiones if f"{dim}_SCORE" in df.columns]
        df["score_activo"] = df[score_cols].sum(axis=1)

        sources_in_dims = catalogo[
            catalogo["included_in_index"] & catalogo["dimension_id"].isin(dimensiones)
        ]["source_id"].nunique()
        df["indicadores_activos"] = sources_in_dims
        df["score_label"] = get_score_label(dimensiones=dimensiones)

    if assign_level:
        df["intensidad_activa"] = score_values_to_level(df["score_activo"].values)
        df["riesgo_activo"] = df["intensidad_activa"]

    return df


def build_department_active(
    municipios_activos: pd.DataFrame,
    departamentos: pd.DataFrame,
    dimensiones: List[str] | None = None,
    fuentes: List[str] | None = None,
    assign_level: bool = True,
) -> pd.DataFrame:
    """
    Calcula el score activo departamental como promedio ponderado por población de sus municipios.
    """
    df = departamentos.copy()
    dimensiones = [d for d in (dimensiones or []) if d in DIMENSIONES_TERRITORIALES]
    fuentes = fuentes or []

    # Caso 1: Sin filtros
    if not dimensiones and not fuentes:
        df["score_activo"] = df["INDICE_TERRITORIAL_DEPTO"]
        df["intensidad_activa"] = df["intensidad_territorial_depto"].fillna("Bajo")
        df["riesgo_activo"] = df["intensidad_activa"]
        df["score_label"] = get_score_label()
        return df

    # Caso con filtros: Promedio ponderado por población municipal
    def calc_weighted(group: pd.DataFrame) -> float:
        weights = group["poblacion_total"].clip(lower=1.0)
        return float(np.average(group["score_activo"], weights=weights))

    grouped = (
        municipios_activos.groupby("cod_dpto")
        .apply(calc_weighted)
        .reset_index(name="score_activo")
    )

    df = df.drop(columns=["score_activo"], errors="ignore").merge(
        grouped, on="cod_dpto", how="left"
    )
    df["score_activo"] = df["score_activo"].fillna(0.0)
    df["score_label"] = get_score_label(dimensiones=dimensiones)

    if assign_level:
        df["intensidad_activa"] = score_values_to_level(df["score_activo"].values)
        df["riesgo_activo"] = df["intensidad_activa"]

    return df
