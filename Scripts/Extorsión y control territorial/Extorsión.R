# URL del dataset
url_extorsion <- "https://www.datos.gov.co/resource/q2ib-t9am.json"


# Consulta SoQL
EXTORSION <- request(url_extorsion) |>
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



