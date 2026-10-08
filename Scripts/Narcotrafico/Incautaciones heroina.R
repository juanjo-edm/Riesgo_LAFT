# URL del dataset
url_incautacion_heroina <- "https://www.datos.gov.co/resource/iat2-gskt.json"


# Consulta SoQL
INCAUTACION_HEROINA <- request(url_incautacion_heroina) |>
  req_url_query(
    `$query` = glue("
      SELECT *
      WHERE fecha_hecho >= '{fecha_limite}'
        AND cod_depto IS NOT NULL
        AND cod_muni IS NOT NULL
        AND length(cod_depto) = 2
        AND length(cod_muni) = 5
      LIMIT 1000000
    ")
  ) |>
  req_perform() |>
  resp_body_json(simplifyVector = TRUE) |>
  as_tibble()


colnames(INCAUTACION_HEROINA)

distinct(INCAUTACION_HEROINA,unidad)

depto <- distinct(INCAUTACION_HEROINA,departamento)



n_distinct(INCAUTACION_HEROINA$departamento)
