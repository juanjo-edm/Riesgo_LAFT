# URL del dataset
url_insumos_liquidos <- "https://www.datos.gov.co/resource/k2wp-tdv7.json"

# Consulta SoQL
INSUMOS_LIQUIDOS <- request(url_insumos_liquidos) |>
  req_url_query(
    `$query` = glue("
      SELECT *
      WHERE fecha_hecho >= '{fecha_limite}'
      AND unidad == 'GALON'
      LIMIT 1000000
    ")
  ) |>
  req_perform() |>
  resp_body_json(simplifyVector = TRUE) |>
  as_tibble()





colnames(INSUMOS_LIQUIDOS)

# Calcular  por municipio
INSUMOS_LIQUIDOS_NARC <-  INSUMOS_LIQUIDOS |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,cod_muni) |> 
  summarise(
    delitos_insumo_liquido_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    delitos_insumo_liquido_totales = sum(cantidad, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_insumo_liquido_promedio = round(delitos_insumo_liquido_promedio,0)
  )
