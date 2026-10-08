"""
ETL Pipeline para procesar los datos del Atlas Territorial LAFT y convertirlos a Parquet.
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np

# Permitir importar desde src
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import (
    RAW_DIR,
    PROCESSED_DIR,
    OUTPUT_DIR,
    DIMENSIONES_TERRITORIALES,
    DIMENSION_LABELS,
    DIMENSION_SCORE_COLS,
    INTENSIDAD_LEVELS,
)


def format_cod_mpio(val) -> str:
    """Formatea código municipal a 5 dígitos con ceros a la izquierda."""
    try:
        num = int(float(val))
        return f"{num:05d}"
    except (ValueError, TypeError):
        return str(val).strip().zfill(5)


def format_cod_dpto(val) -> str:
    """Formatea código departamental a 2 dígitos con ceros a la izquierda."""
    try:
        num = int(float(val))
        return f"{num:02d}"
    except (ValueError, TypeError):
        return str(val).strip().zfill(2)


def prepare_data(excel_path: Path | None = None) -> None:
    """Lee el libro de Excel consolidado y genera los archivos .parquet procesados."""
    if excel_path is None:
        if (RAW_DIR / "atlas_territorial_publico.xlsx").exists():
            excel_path = RAW_DIR / "atlas_territorial_publico.xlsx"
        elif (OUTPUT_DIR / "atlas_territorial_publico.xlsx").exists():
            excel_path = OUTPUT_DIR / "atlas_territorial_publico.xlsx"
        else:
            raise FileNotFoundError(
                "No se encontró atlas_territorial_publico.xlsx en data/raw/ ni en Output/"
            )

    print(f"📖 Leyendo libro público desde: {excel_path}")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Catálogo de indicadores
    print("  -> Procesando CATALOGO_INDICADORES...")
    catalogo = pd.read_excel(excel_path, sheet_name="CATALOGO_INDICADORES")
    catalogo["dimension_id"] = catalogo["dimension_id"].astype(str)
    catalogo["source_id"] = catalogo["source_id"].astype(str)
    catalogo["included_in_index"] = catalogo["included_in_index"].astype(bool)
    catalogo["dimension_order"] = catalogo["dimension_order"].astype(int)
    catalogo["source_order"] = catalogo["source_order"].astype(int)
    catalogo = catalogo.sort_values(["dimension_order", "source_order"]).reset_index(drop=True)
    catalogo.to_parquet(PROCESSED_DIR / "catalogo_indicadores.parquet", index=False)

    # 2. Municipios total
    print("  -> Procesando TOTAL_TERRITORIAL (municipios)...")
    municipios = pd.read_excel(excel_path, sheet_name="TOTAL_TERRITORIAL")
    municipios["cod_dpto"] = municipios["cod_dpto"].apply(format_cod_dpto)
    municipios["cod_mpio"] = municipios["cod_mpio"].apply(format_cod_mpio)
    municipios["poblacion_total"] = pd.to_numeric(municipios["poblacion_total"], errors="coerce").fillna(0)
    municipios["INDICE_TERRITORIAL"] = pd.to_numeric(municipios["INDICE_TERRITORIAL"], errors="coerce").fillna(0.0)
    municipios["INDICE_TERRITORIAL_Z"] = pd.to_numeric(municipios["INDICE_TERRITORIAL_Z"], errors="coerce").fillna(0.0)

    # Asegurar que todas las columnas de score y dimensión existan numéricamente
    for dim in DIMENSIONES_TERRITORIALES:
        score_col = f"{dim}_SCORE"
        intensidad_col = f"{dim}_INTENSIDAD"
        if score_col in municipios.columns:
            municipios[score_col] = pd.to_numeric(municipios[score_col], errors="coerce").fillna(0.0)
        else:
            municipios[score_col] = 0.0

        if intensidad_col in municipios.columns:
            municipios[intensidad_col] = pd.to_numeric(municipios[intensidad_col], errors="coerce").fillna(0.0)
        else:
            municipios[intensidad_col] = 0.0

    municipios.to_parquet(PROCESSED_DIR / "municipios_total.parquet", index=False)

    # 3. Departamentos total
    print("  -> Procesando TOTAL_TERRITORIAL_DEPTO (departamentos)...")
    departamentos = pd.read_excel(excel_path, sheet_name="TOTAL_TERRITORIAL_DEPTO")
    departamentos["cod_dpto"] = departamentos["cod_dpto"].apply(format_cod_dpto)
    departamentos["INDICE_TERRITORIAL_DEPTO"] = pd.to_numeric(departamentos["INDICE_TERRITORIAL_DEPTO"], errors="coerce").fillna(0.0)
    departamentos["poblacion_total_depto"] = pd.to_numeric(departamentos["poblacion_total_depto"], errors="coerce").fillna(0)
    departamentos["municipios_total"] = pd.to_numeric(departamentos["municipios_total"], errors="coerce").fillna(0).astype(int)
    departamentos.to_parquet(PROCESSED_DIR / "departamentos_total.parquet", index=False)

    # 4. Indicadores municipales (tabla larga)
    print("  -> Procesando INDICADORES_MUNICIPALES...")
    indicadores = pd.read_excel(excel_path, sheet_name="INDICADORES_MUNICIPALES")
    indicadores["cod_dpto"] = indicadores["cod_dpto"].apply(format_cod_dpto)
    indicadores["cod_mpio"] = indicadores["cod_mpio"].apply(format_cod_mpio)
    indicadores["dimension_id"] = indicadores["dimension_id"].astype(str)
    indicadores["source_id"] = indicadores["source_id"].astype(str)
    indicadores["total"] = pd.to_numeric(indicadores["total"], errors="coerce").fillna(0.0)
    indicadores["tasa"] = pd.to_numeric(indicadores["tasa"], errors="coerce").fillna(0.0)
    indicadores["z_score"] = pd.to_numeric(indicadores["z_score"], errors="coerce").fillna(0.0)
    indicadores["z_score_winsor"] = pd.to_numeric(indicadores["z_score_winsor"], errors="coerce").fillna(0.0)
    indicadores["source_score_norm"] = pd.to_numeric(indicadores["source_score_norm"], errors="coerce").fillna(0.0)
    indicadores["source_score"] = pd.to_numeric(indicadores["source_score"], errors="coerce").fillna(0.0)
    indicadores["included_in_index"] = indicadores["included_in_index"].astype(bool)
    indicadores.to_parquet(PROCESSED_DIR / "indicadores_municipales.parquet", index=False)

    # 5. Dimensiones municipales (tabla larga municipio-dimensión para perfiles)
    print("  -> Construyendo dimensiones_municipales...")
    score_cols = [f"{dim}_SCORE" for dim in DIMENSIONES_TERRITORIALES]
    dim_long = municipios[["cod_dpto", "dpto", "cod_mpio", "nom_mpio"] + score_cols].melt(
        id_vars=["cod_dpto", "dpto", "cod_mpio", "nom_mpio"],
        value_vars=score_cols,
        var_name="dimension_score",
        value_name="score"
    )
    dim_long["dimension_id"] = dim_long["dimension_score"].str.replace("_SCORE", "", regex=False)
    dim_long["dimension_label"] = dim_long["dimension_id"].map(DIMENSION_LABELS).fillna(dim_long["dimension_id"])
    dim_long["score"] = pd.to_numeric(dim_long["score"], errors="coerce").fillna(0.0)
    dim_long = dim_long.drop(columns=["dimension_score"])
    dim_long.to_parquet(PROCESSED_DIR / "dimensiones_municipales.parquet", index=False)

    # 6. Pesos objetivos si existe
    if "PESOS_OBJETIVOS_TERRITORIAL" in pd.ExcelFile(excel_path).sheet_names:
        print("  -> Procesando PESOS_OBJETIVOS_TERRITORIAL...")
        pesos = pd.read_excel(excel_path, sheet_name="PESOS_OBJETIVOS_TERRITORIAL", skiprows=2)
        for col in pesos.columns:
            if "fecha" in col.lower():
                pesos[col] = pesos[col].astype(str)
            elif col in ["peso", "peso_pct"]:
                pesos[col] = pd.to_numeric(pesos[col], errors="coerce").fillna(0.0)
            elif col == "escenario_oficial":
                pesos[col] = pesos[col].astype(bool)
            else:
                pesos[col] = pesos[col].astype(str)
        pesos.to_parquet(PROCESSED_DIR / "pesos_objetivos.parquet", index=False)

    print("\n✅ Datos Parquet preparados exitosamente en data/processed/:")
    print(f"  - Municipios: {len(municipios)} filas")
    print(f"  - Departamentos: {len(departamentos)} filas")
    print(f"  - Indicadores detallados: {len(indicadores)} filas")
    print(f"  - Dimensiones largas: {len(dim_long)} filas")
    print(f"  - Catálogo de fuentes: {len(catalogo)} registros")


if __name__ == "__main__":
    prepare_data()
