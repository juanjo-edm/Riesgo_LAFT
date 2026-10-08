# URL del dataset
url_incautacion_coca <- "https://www.datos.gov.co/resource/26zg-9p9r.json"


# Consulta SoQL
INCAUCTACION_COCA <- request(url_incautacion_coca) |>
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



colnames(INCAUCTACION_COCA)

# Calcular  por municipio
INCAUCTACION_COCA_NARC <-  INCAUCTACION_COCA |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,cod_muni) |> 
  summarise(
    delitos_incautaciones_cocaina_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    delitos_incautaciones_cocaina_totales = sum(cantidad, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_incautaciones_cocaina_promedio = round(delitos_incautaciones_cocaina_promedio,0)
  )
