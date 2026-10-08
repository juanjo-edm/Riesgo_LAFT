# URL del dataset
url_cultivos_ilicitos <- "https://www.datos.gov.co/resource/acs4-3wgp.json"


# Consulta SoQL
CULTUVOS_ILICITOS <- request(url_cultivos_ilicitos) |>
  req_url_query(
    `$query` = glue("
      SELECT *
      LIMIT 100000
    ")
  ) |>
  req_perform() |>
  resp_body_json(simplifyVector = TRUE) |>
  as_tibble()


# Acomodamos a formato largo
CULTUVOS_ILICITOS_1 <- CULTUVOS_ILICITOS %>%
  pivot_longer(
    cols = starts_with("_"),
    names_to = "anio",
    values_to = "cantidad"
  ) |> 
  mutate(
    anio = str_remove(anio,"_"),
    anio = as.numeric(anio),
    cantidad = as.numeric(cantidad)
  ) |> 
  dplyr::filter(anio >= anio_limite)



# Calcular  por municipio
CULTUVOS_ILICITOS_NARC <-  CULTUVOS_ILICITOS_1 |> 
  mutate(
    cantidad = as.numeric(cantidad)
  ) |> 
  group_by(municipio,codmpio) |> 
  summarise(
    delitos_cultivo_promedio = mean(cantidad[!is.na(cantidad) & cantidad != 0], na.rm = TRUE),
    delitos_cultivo_totales = sum(cantidad, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_cultivo_promedio = round(delitos_cultivo_promedio,0)
  )

