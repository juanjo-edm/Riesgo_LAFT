# URL del dataset
url_insumos_solidos <- "https://www.datos.gov.co/resource/n997-hhiv.json"

# Consulta SoQL
INSUMOS_SOLIDOS <- request(url_insumos_solidos) |>
  req_url_query(
    `$query` = glue("
      SELECT *
      WHERE fecha_hecho >= '{fecha_limite}'
      AND unidad == 'KILOGRAMO'
      LIMIT 1000000
    ")
  ) |>
  req_perform() |>
  resp_body_json(simplifyVector = TRUE) |>
  as_tibble()





colnames(INSUMOS_SOLIDOS)
distinct(INSUMOS_SOLIDOS,unidad)

# Calcular  por municipio
INSUMOS_SOLIDOS_NARC <-  INSUMOS_SOLIDOS |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,cod_muni) |> 
  summarise(
    delitos_insumo_solido_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    delitos_insumo_solido_totales = sum(cantidad, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_insumo_solido_promedio = round(delitos_insumo_solido_promedio,0)
  )
