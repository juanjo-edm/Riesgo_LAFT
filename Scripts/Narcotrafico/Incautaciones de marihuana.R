# URL del dataset
url_incautacion_marihuana <- "https://www.datos.gov.co/resource/g228-vp9d.json"


# Consulta SoQL
INCAUCTACION_MARIHUANA <- request(url_incautacion_marihuana) |>
  req_url_query(
    `$query` = glue("
      SELECT *
      WHERE fecha_hecho >= '{fecha_limite}'
      LIMIT 1000000
    ")
  ) |>
  req_perform() |>
  resp_body_json(simplifyVector = TRUE) |>
  as_tibble()



colnames(INCAUCTACION_MARIHUANA)

# Calcular  por municipio
INCAUCTACION_COCA_NARC <-  INCAUCTACION_MARIHUANA |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,cod_muni) |> 
  summarise(
    delitos_incautaciones_marihuana_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    delitos_incautaciones_marihuana_totales = sum(cantidad, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_incautaciones_marihuana_promedio = round(delitos_incautaciones_marihuana_promedio,0)
  )
