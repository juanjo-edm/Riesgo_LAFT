# URL del dataset
url_capturas_mineria <- "https://www.datos.gov.co/resource/3wcs-8xp9.json"


# Consulta SoQL
CAPTURAS_MINERIA <- request(url_capturas_mineria) |>
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


colnames(CAPTURAS_MINERIA)
distinct(CAPTURAS_MINERIA,unidad_de_medida)

Validacion <-  CAPTURAS_MINERIA |> 
  mutate(
    unidad_de_medida = as.numeric(unidad_de_medida),
    cantidad = as.numeric(cantidad)
  ) |> 
  dplyr::filter(
    unidad_de_medida != cantidad
  )
