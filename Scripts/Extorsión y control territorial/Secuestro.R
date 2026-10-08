# URL del dataset
url_secuestro <- "https://www.datos.gov.co/resource/d7zw-hpf4.json"


# Consulta SoQL
SECUESTRO <- request(url_secuestro) |>
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
