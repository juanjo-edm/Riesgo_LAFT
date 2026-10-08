# URL del dataset
url_base_coca <- "https://www.datos.gov.co/resource/nxbk-nikm.json"


# Consulta SoQL
BASE_DE_COCA <- request(url_base_coca) |>
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
BASE_DE_COCA_NARC <-  BASE_DE_COCA |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,cod_muni) |> 
  summarise(
    delitos_base_coca_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    delitos_base_coca_totales = sum(cantidad, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_base_coca_promedio = round(delitos_base_coca_promedio,0)
  )
