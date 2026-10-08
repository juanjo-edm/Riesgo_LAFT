# URL del dataset
url_maquinarias_ilicitas <- "https://www.datos.gov.co/resource/dxs6-mdeg.json"


# Consulta SoQL
MAQUINARIA_ILEGAL <- request(url_maquinarias_ilicitas) |>
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


distinct(MAQUINARIA_ILEGAL,unidad_de_medida)
