# URL del dataset
url_incautacion_basuco <-  "https://www.datos.gov.co/resource/3cjd-phaj.json"

# Consulta SoQL
INCAUTACION_BASUCO <- request(url_incautacion_basuco) |>
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

# Calcular  por municipio
INCAUTACION_BASUCO_NARC <-  INCAUTACION_BASUCO |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,cod_muni) |> 
  summarise(
    delitos_incautaciones_basuco_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    delitos_incautaciones_basuco_totales = sum(cantidad, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_incautaciones_basuco_promedio = round(delitos_incautaciones_basuco_promedio,0)
  )
