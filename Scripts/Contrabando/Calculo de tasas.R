library(dplyr)
library(stringr)
library(readr)
library(tidyr)

# 1) Define años de exposición (Ajústalo a tu ventana real)
A_exposicion <- tiempo_años  # ej: 2016-2026

CONT_DF_2 <- CONT_DF_1 %>%
  mutate(
    # 2) Limpieza mínima: NA -> 0 en totales (si NA significa "sin casos")
    Contrabando_casos_totales = coalesce(Contrabando_casos_totales, 0),
    Pirateria_casos_totales   = coalesce(Pirateria_casos_totales, 0),
    
    # 3) Validaciones básicas de población
    poblacion_total = as.numeric(poblacion_total),
    
    # 4) Tasa anualizada por 100.000 (incidencia con exposición)
    tasa_contrabando = if_else(
      is.na(poblacion_total) | poblacion_total <= 0,
      NA_real_,
      (Contrabando_casos_totales / (poblacion_total * A_exposicion)) * 100000
    ),
    
    tasa_pirateria= if_else(
      is.na(poblacion_total) | poblacion_total <= 0,
      NA_real_,
      (Pirateria_casos_totales / (poblacion_total * A_exposicion)) * 100000
    ),
    
    # 5) Tasa combinada (sumas de eventos / misma población y exposición)
    laft_casos_totales = Contrabando_casos_totales + Pirateria_casos_totales,
    tasa_laft_total_contrabando = if_else(
      is.na(poblacion_total) | poblacion_total <= 0,
      NA_real_,
      (laft_casos_totales / (poblacion_total * A_exposicion)) * 100000
    )
  )





library(dplyr)
library(tidyr)

CONT_TASAS_LONG <- CONT_DF_2 %>%
  # 1) Nos quedamos con lo necesario
  select(
    cod_dpto, dpto, cod_mpio, nom_mpio, poblacion_total,
    Contrabando_casos_totales, Pirateria_casos_totales,
    tasa_contrabando_100k, tasa_pirateria_100k
  ) %>%
  # 2) Estandarizamos nombres para que todos queden "metrica_delito"
  rename(
    casos_totales_contrabando = Contrabando_casos_totales,
    casos_totales_pirateria   = Pirateria_casos_totales,
    tasa_100k_contrabando     = tasa_contrabando_100k,
    tasa_100k_pirateria       = tasa_pirateria_100k
  ) %>%
  # 3) Limpieza mínima (si NA en totales significa "0 casos")
  mutate(
    casos_totales_contrabando = coalesce(casos_totales_contrabando, 0),
    casos_totales_pirateria   = coalesce(casos_totales_pirateria, 0)
  ) %>%
  # 4) Pivot: 2 grupos EXACTOS => (metrica)_(delito)
  pivot_longer(
    cols = c(casos_totales_contrabando, casos_totales_pirateria,
             tasa_100k_contrabando, tasa_100k_pirateria),
    names_to = c(".value", "delito"),
    names_pattern = "^(casos_totales|tasa_100k)_(contrabando|pirateria)$"
  ) %>%
  # 5) Etiquetas bonitas
  mutate(
    delito = recode(delito,
                    contrabando = "Contrabando",
                    pirateria   = "Piratería")
  )



CONT_DF_2 %>%
  arrange(desc(tasa_laft_total_100k)) %>%
  select(cod_mpio, nom_mpio, poblacion_total, laft_casos_totales, tasa_laft_total_100k) %>%
  slice_head(n = 10)

CONT_DF_2 %>%
  summarise(
    n_total = n(),
    n_pob_na = sum(is.na(poblacion_total)),
    n_pob_cero = sum(poblacion_total <= 0, na.rm = TRUE),
    n_tasa_na = sum(is.na(tasa_laft_total_100k))
  )
