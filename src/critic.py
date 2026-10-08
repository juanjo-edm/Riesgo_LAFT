"""
Implementación del método de ponderación objetiva CRITIC
(Criteria Importance Through Intercriteria Correlation).
"""

from typing import Dict, Sequence, Tuple
import numpy as np
import pandas as pd


def winsorize_series(
    series: pd.Series, probs: Tuple[float, float] = (0.01, 0.99)
) -> pd.Series:
    """
    Winsoriza una serie numérica a los percentiles indicados (por defecto 1% y 99%).
    """
    clean = pd.to_numeric(series, errors="coerce")
    lower = clean.quantile(probs[0])
    upper = clean.quantile(probs[1])
    return clean.clip(lower=lower, upper=upper)


def minmax_scale(series: pd.Series) -> pd.Series:
    """
    Normalización Min-Max al intervalo [0, 1].
    """
    clean = pd.to_numeric(series, errors="coerce")
    min_val = clean.min()
    max_val = clean.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(0.0, index=series.index)

    return (clean - min_val) / (max_val - min_val)


def calculate_critic_weights(
    df: pd.DataFrame, method: str = "pearson"
) -> Dict[str, float]:
    """
    Calcula los pesos objetivos CRITIC para una matriz de dimensiones o indicadores.

    CRITIC pondera positivamente la variabilidad (desviación estándar) y
    penaliza la redundancia (suma de correlaciones con otras dimensiones):
        C_j = sigma_j * sum_{k=1}^m (1 - r_{jk})
        w_j = C_j / sum(C_k)
    """
    # 1. Normalizar cada columna con Min-Max
    norm_df = df.apply(minmax_scale)

    # 2. Matriz de correlación
    corr_matrix = norm_df.corr(method=method).fillna(0.0).to_numpy(copy=True)
    np.fill_diagonal(corr_matrix, 1.0)

    # 3. Desviación estándar de cada criterio
    std_devs = norm_df.std(ddof=1).fillna(0.0).to_numpy(copy=True)

    # 4. Cantidad de información C_j
    # sum_{k=1}^m (1 - r_{jk})
    conflict = np.sum(1.0 - corr_matrix, axis=1)
    information = std_devs * conflict

    total_info = np.sum(information)
    cols = list(df.columns)

    if total_info <= 0 or not np.isfinite(total_info):
        # Asignación uniforme si no hay contraste
        uniform_weight = 1.0 / len(cols) if cols else 0.0
        return {col: uniform_weight for col in cols}

    weights = information / total_info
    return {col: float(weight) for col, weight in zip(cols, weights)}
