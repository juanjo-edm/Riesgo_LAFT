"""
Carga y acceso a datos procesados (Parquet) y capas geoespaciales (GeoJSON).
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict
import json
import pandas as pd
import geopandas as gpd

from src.config import PROCESSED_DIR, GEODATA_DIR


class DataLoader:
    """Clase para cargar y almacenar en caché los conjuntos de datos de la aplicación."""

    def __init__(self, data_dir: Path = PROCESSED_DIR, geodata_dir: Path = GEODATA_DIR):
        self.data_dir = data_dir
        self.geodata_dir = geodata_dir
        self._data: Dict[str, Any] = {}

    def load_all(self) -> Dict[str, Any]:
        """Carga todos los conjuntos de datos tabulares y geoespaciales."""
        if not self._data:
            print(f"[INFO] Cargando conjuntos de datos Parquet desde {self.data_dir}...")
            if not self.data_dir.exists():
                raise FileNotFoundError(f"No se encontró el directorio de datos procesados: {self.data_dir}")
            self._data["municipios"] = pd.read_parquet(self.data_dir / "municipios_total.parquet")
            self._data["departamentos"] = pd.read_parquet(self.data_dir / "departamentos_total.parquet")
            self._data["indicadores_municipales"] = pd.read_parquet(self.data_dir / "indicadores_municipales.parquet")
            self._data["dimensiones_municipales"] = pd.read_parquet(self.data_dir / "dimensiones_municipales.parquet")
            self._data["catalogo_indicadores"] = pd.read_parquet(self.data_dir / "catalogo_indicadores.parquet")

            # Carga de capas geoespaciales (GeoParquet ultra rápido o GeoJSON)
            geo_mpios_parquet = self.geodata_dir / "mapa_municipios.parquet"
            geo_dptos_parquet = self.geodata_dir / "mapa_departamentos.parquet"
            geo_mpios_json = self.geodata_dir / "mapa_municipios.geojson"
            geo_dptos_json = self.geodata_dir / "mapa_departamentos.geojson"

            if geo_mpios_parquet.exists():
                self._data["mapa_municipios"] = gpd.read_parquet(geo_mpios_parquet)
            elif geo_mpios_json.exists():
                self._data["mapa_municipios"] = gpd.read_file(geo_mpios_json, engine="pyogrio")
            else:
                self._data["mapa_municipios"] = None

            if geo_dptos_parquet.exists():
                self._data["mapa_departamentos"] = gpd.read_parquet(geo_dptos_parquet)
            elif geo_dptos_json.exists():
                self._data["mapa_departamentos"] = gpd.read_file(geo_dptos_json, engine="pyogrio")
            else:
                self._data["mapa_departamentos"] = None

            print("[OK] Datos cargados correctamente en memoria.")

        return self._data


# Instancia singleton para la aplicación
_loader_instance: DataLoader | None = None


def get_data_loader() -> DataLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DataLoader()
    return _loader_instance


def load_app_data() -> Dict[str, Any]:
    """Acceso rápido a los datos de la app."""
    return get_data_loader().load_all()
