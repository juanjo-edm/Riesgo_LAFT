library(httr2)
library(tidyverse)
library(lubridate)
library(glue)

tiempo_años <- 5

# URL del dataset
url_pirateria_terrestre <- "https://www.datos.gov.co/resource/sutf-7dyz.json"


# Consulta SoQL
PIRATERIA_TERRESTRE <- request(url_pirateria_terrestre) |>
  req_url_query(
    `$query` = glue("
      SELECT *
      WHERE fecha_hecho >= '{fecha_limite}'
      LIMIT 100000
    ")
  ) |>
  req_perform() |>
  resp_body_json(simplifyVector = TRUE) |>
  as_tibble()

colnames(PIRATERIA_TERRESTRE)

# Calcular promedio por municipio
CONT_EVE_PIRT <-  PIRATERIA_TERRESTRE |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,cod_muni) |> 
  summarise(
    Pirateria_casos_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    Pirateria_casos_promedio = round(Pirateria_casos_promedio,0)
  )
