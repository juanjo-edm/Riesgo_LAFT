"""
Configuración global, constantes y etiquetas del Atlas Territorial de Riesgo LAFT.
"""

from pathlib import Path

# Directorios de datos con resolución insensible a mayúsculas para Linux / Posit Connect
BASE_DIR = Path(__file__).resolve().parent.parent

def _resolve_dir(base: Path, candidates: list[str]) -> Path:
    for name in candidates:
        target = base / name
        if target.is_dir():
            return target
    return base / candidates[0]

DATA_DIR = _resolve_dir(BASE_DIR, ["Data", "data"])
RAW_DIR = _resolve_dir(DATA_DIR, ["raw", "Raw"])
PROCESSED_DIR = _resolve_dir(DATA_DIR, ["processed", "Processed"])
GEODATA_DIR = _resolve_dir(DATA_DIR, ["geodata", "Geodata"])
OUTPUT_DIR = _resolve_dir(BASE_DIR, ["Output", "output"])

# Dimensiones territoriales oficiales
DIMENSIONES_TERRITORIALES = [
    "CONT", "CORR", "AMBI", "EXTC", "MIEX", "NARC", "TFT", "TRAT",
    "HURTO", "HOMICIDIOS", "VIOLENCIA_SEXUAL", "ARMAS", "CAPTURAS"
]

DIMENSION_LABELS = {
    "CONT": "Contrabando y economías ilícitas",
    "CORR": "Corrupción pública",
    "AMBI": "Delitos ambientales",
    "EXTC": "Extorsión y secuestro",
    "MIEX": "Minería ilegal",
    "NARC": "Narcotráfico",
    "TFT": "Terrorismo y eventos asociados",
    "TRAT": "Trata y migración irregular",
    "HURTO": "Hurto",
    "HOMICIDIOS": "Homicidios",
    "VIOLENCIA_SEXUAL": "Violencia sexual",
    "ARMAS": "Armas",
    "CAPTURAS": "Capturas",
}

# Niveles y colores de intensidad de riesgo
INTENSIDAD_LEVELS = ["Bajo", "Medio", "Alto", "Muy alto"]

INTENSIDAD_PALETTE = {
    "Bajo": "#8BC34A",       # Verde
    "Medio": "#F2C94C",      # Amarillo
    "Alto": "#F2994A",       # Naranja
    "Muy alto": "#D7191C",   # Rojo
}

# Columnas de puntuación de dimensiones en la tabla municipal
DIMENSION_SCORE_COLS = {dim: f"{dim}_SCORE" for dim in DIMENSIONES_TERRITORIALES}
DIMENSION_INTENSIDAD_COLS = {dim: f"{dim}_INTENSIDAD" for dim in DIMENSIONES_TERRITORIALES}

# Metadatos territoriales estándar
METADATA_COLS = [
    "cod_dpto", "dpto", "cod_mpio", "nom_mpio",
    "tipo_municipio", "longitud", "latitud", "poblacion_total"
]
