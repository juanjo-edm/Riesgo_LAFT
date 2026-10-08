# URL del dataset
url_minas_intervenidas <- "https://www.datos.gov.co/resource/gr35-i7pm.json"


# Consulta SoQL
MINAS_ILEGALES <- request(url_minas_intervenidas) |>
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


