# URL del dataset
url_destruccion_laboratorios <- "https://www.datos.gov.co/resource/s29y-2xjd.json"


# Consulta SoQL
DESTRUCCION_LABORATORIOS <- request(url_destruccion_laboratorios) |>
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



colnames(DESTRUCCION_LABORATORIOS)

# Calcular  por municipio
DESTRUCCION_LABORATORIOS_NARC <-  DESTRUCCION_LABORATORIOS |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,cod_muni) |> 
  summarise(
    delitos_destruccion_laboratorios_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    delitos_destruccion_laboratorios_totales = sum(cantidad, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_destruccion_laboratorios_promedio = round(delitos_destruccion_laboratorios_promedio,0)
  )
