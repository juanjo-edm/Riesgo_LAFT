"""
Configuración global, constantes y etiquetas del Atlas Territorial de Riesgo LAFT.
"""

from pathlib import Path

# Directorios de datos
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GEODATA_DIR = DATA_DIR / "geodata"
OUTPUT_DIR = BASE_DIR / "Output"

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
