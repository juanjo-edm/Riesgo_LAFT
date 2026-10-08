library(tidyverse)
library(readxl)

# 1. Leemos archivo excel 
path <- "Data/PERSONAS_DEMOGRAFICO_Cuadros_CNPV_2018.xlsx"
df_1pm <- read_excel(path, sheet = "1PM")

# 2. Ajustamos para lee datos de la poblacion
pob_municipio <- df_1pm |>
  dplyr::filter(!is.na(...2), ...3 == "Total", ...4 == "Total") |>
  select(municipio = ...2, poblacion_total = ...5) |>
  separate(municipio, into = c("cod_divipola", "nombre_municipio"), sep = "_", extra = "merge") |>
  mutate(poblacion_total = as.integer(poblacion_total))


colnames(pob_municipio)
glimpse(pob_municipio)

# 4. Añadimos municipio de NUEVO BELÉN DE BAJIRÁ"



# Cremos observacion de nuevo municipio
nueva_obs <- tibble(
  cod_divipola = "27493",
  nombre_municipio = "NUEVO BELÉN DE BAJIRÁ",
  poblacion_total = 13L
)

pob_municipio <- pob_municipio %>%
  mutate(
    cod_divipola = as.character(cod_divipola),
    poblacion_total = as.integer(poblacion_total)
  ) %>%
  bind_rows(nueva_obs) %>%
  arrange(cod_divipola)

# 3. Validamos 
print(paste("La población total es:", sum(pob_municipio$poblacion_total, na.rm = TRUE)))
