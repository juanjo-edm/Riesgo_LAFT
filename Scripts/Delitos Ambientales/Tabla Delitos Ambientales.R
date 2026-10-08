# 1) Cargar datos  -----
# Indicamos url de la api
url_procesos_fiscalia_dca <-  "https://www.datos.gov.co/resource/9zck-qfvc.json"


# Nos conectamos con la tabla
DELITOS_AMBIENTALES <- request(url_procesos_fiscalia_dca) |>
  req_url_query(
    `$query` = glue("
    SELECT *
    WHERE
    fecha_hecho >= '{fecha_limite}'
    LIMIT 1000000
    ")
  ) |>
  req_perform() |>
  resp_body_json(simplifyVector = TRUE) |>
  as_tibble()


# Vemos resultado
colnames(DELITOS_AMBIENTALES)
glimpse(DELITOS_AMBIENTALES)
