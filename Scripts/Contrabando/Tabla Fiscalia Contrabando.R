library(httr2)
library(tidyverse)
library(conflicted)
library(tibble)

library(dplyr)
library(stringr)
library(stringi)
library(tibble)



# 1) Cargar datos de filscalia -----

url_procesos_fiscalia <-  "https://www.datos.gov.co/resource/6d52-qyqg.json"




# Casos de contrabando  que NO terminaron archivados ni precluidos y que están en etapas muy avanzadas (ejecución de penas / terminación anticipada).

PROCESOS_FISCALIA <-  request(url_procesos_fiscalia) |> 
  req_url_query(
    `$query` = glue("
    SELECT *
    WHERE
    criminalidad = 'SI'
    AND es_archivo = 'NO'
    AND es_preclusion = 'NO'
    AND etapa_caso  IN ('EJECUCIÓN DE PENAS','TERMINACIÓN ANTICIPADA')   
    AND lower(delito) LIKE '%contraband%'
    AND a_o_hechos >= '{anio_limite}'
    ")
  ) |> 
  req_perform() |> 
  resp_body_json(simplifyVector = TRUE) |> 
  as_tibble()




colnames(PROCESOS_FISCALIA)
dim(PROCESOS_FISCALIA)

distinct(PROCESOS_FISCALIA,a_o_hechos)
distinct(PROCESOS_FISCALIA,es_archivo)
distinct(PROCESOS_FISCALIA,es_preclusion)
distinct(PROCESOS_FISCALIA,estado)
distinct(PROCESOS_FISCALIA,etapa_caso)

distinct(PROCESOS_FISCALIA,delito)





delitos <- distinct(PROCESOS_FISCALIA,delito)
municipios <- distinct(PROCESOS_FISCALIA,municipio_hecho)
departamento <- distinct(PROCESOS_FISCALIA,departamento_hecho)


# 2) Cargar datos de DIVIPOLA -----

# https://www.datos.gov.co/Mapas-Nacionales/DIVIPOLA-C-digos-municipios/gdxc-w37w/about_data


url_divipola <-  "https://www.datos.gov.co/resource/gdxc-w37w.json"


# Casos de contrabando  que NO terminaron archivados ni precluidos y que están en etapas muy avanzadas (ejecución de penas / terminación anticipada).

TABLA_DIVIPOLA <-  request(url_divipola) |> 
  req_url_query(
    `$query` = "
    SELECT *
    LIMIT 100000
    "
  ) |> 
  req_perform() |> 
  resp_body_json(simplifyVector = TRUE) |> 
  as_tibble()



# 3) Cruzar datos-----

# Enriquecer PROCESOS_FISCALIA con cod_dpto y cod_mpio (DIVIPOLA)
# Estrategia:
# a) Normalizar nombres (dpto/mpio) en ambas tablas
# b) Corregir casos conocidos con diccionario (dpto+mpio)
# c) Join por llave compuesta (dpto_key + mpio_key)
# d) Auditoría de calidad (matched/unmatched)



# 1) Función de normalización
norm_txt <- function(x) {
  x %>%
    str_trim() %>%
    str_to_upper() %>%
    stringi::stri_trans_general("Latin-ASCII") %>%  # quita tildes
    str_replace_all("[[:punct:]]", " ") %>%         # quita puntuación
    str_replace_all("\\s+", " ") %>%                # colapsa espacios
    str_trim()
}


# 2) Normalizar y crear llaves


# PROCESOS_FISCALIA -> llaves normalizadas
PF <- PROCESOS_FISCALIA %>%
  mutate(
    dpto_key = norm_txt(departamento_hecho),
    mpio_key = norm_txt(municipio_hecho)
  )

# TABLA_DIVIPOLA -> llaves normalizadas
DIV <- TABLA_DIVIPOLA %>%
  mutate(
    dpto_key = norm_txt(dpto),
    mpio_key = norm_txt(nom_mpio)
  )


# 3) Validación de duplicados en DIVIPOLA (llave compuesta)
#    Si hay duplicados, el join podría duplicar filas.
dup_div <- DIV %>%
  count(dpto_key, mpio_key, name = "n") %>%
  dplyr::filter(n > 1)

# Imprime duplicados (si existen)
if (nrow(dup_div) > 0) {
  message("⚠️ OJO: Hay llaves duplicadas en DIVIPOLA (dpto_key + mpio_key). Revisa 'dup_div'.")
  print(dup_div)
} else {
  message("✅ DIVIPOLA: llaves (dpto_key + mpio_key) sin duplicados.")
}


# 4) Diccionario de equivalencias (casos que NO cruzaron)
#    Aplica por dpto + municipio para evitar errores por homónimos.

dic_municipios <- tribble(
  ~dpto_key,                 ~mpio_key,    ~mpio_key_fix,
  "BOLIVAR",                 "CARTAGENA",  "CARTAGENA DE INDIAS",
  "CAUCA",                   "PIENDAMO",   "PIENDAMO TUNIA",
  "CESAR",                   "MANAURE",    "MANAURE BALCON DEL CESAR",
  "NARINO",                  "CUASPUD",    "CUASPUD CARLOSAMA",
  "NARINO",                  "TUMACO",     "SAN ANDRES DE TUMACO",
  "NORTE DE SANTANDER",      "CUCUTA",     "SAN JOSE DE CUCUTA",
  "VALLE DEL CAUCA",         "CALI",       "SANTIAGO DE CALI"
)


# 5) Aplicar diccionario antes del join

PF_fix <- PF %>%
  left_join(dic_municipios, by = c("dpto_key", "mpio_key")) %>%
  mutate(
    mpio_key = coalesce(mpio_key_fix, mpio_key)
  ) %>%
  select(-mpio_key_fix)


# 6) Join final para traer cod_dpto y cod_mpio

PF_enriq <- PF_fix %>%
  left_join(
    DIV %>% select(dpto_key, mpio_key, cod_dpto, cod_mpio),
    by = c("dpto_key", "mpio_key")
  )


# 7) Auditoría de emparejamiento


# 7A) Tasa de match
auditoria_match <- PF_enriq %>%
  summarise(
    total = n(),
    matched = sum(!is.na(cod_mpio)),
    unmatched = sum(is.na(cod_mpio)),
    pct_unmatched = round(100 * unmatched / total, 2)
  )

print(auditoria_match)

# 7B) Lista de no emparejados (para seguir corrigiendo)
no_match <- PF_enriq %>%
  dplyr::filter(is.na(cod_mpio)) %>%
  distinct(departamento_hecho, municipio_hecho, dpto_key, mpio_key) %>%
  arrange(dpto_key, mpio_key)

# Imprime no_match solo si hay algo pendiente
if (nrow(no_match) > 0) {
  message("⚠️ Aún hay registros sin cruce. Revisa 'no_match' para ampliar el diccionario.")
  print(no_match)
} else {
  message("✅ Listo: todos los registros cruzaron con DIVIPOLA (cod_mpio no es NA).")
}




# Calcular promedio por municipio
PF_CONT_1 <-  PF_CONT_enriq |> 
  mutate(
    total_procesos = as.numeric(total_procesos)
  ) |> 
  group_by(municipio_hecho,cod_mpio) |> 
  summarise(
    Contrabando_casos_promedio = mean(total_procesos[!is.na(total_procesos) & total_procesos != 0], na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    Contrabando_casos_promedio = round(Contrabando_casos_promedio,0)
  )

colnames(TABLA_DIVIPOLA)
colnames(PF_CONT_1)
glimpse(TABLA_DIVIPOLA)


#cruzar con tabla de divipola
CONT_DF <-  TABLA_DIVIPOLA |> 
  left_join(
    PF_CONT_1 |> select(-municipio_hecho),
    by = "cod_mpio"
  )

# Remplazar NA por cero
CONT_DF_1 <-  CONT_DF |> 
  mutate(
    Contrabando_casos_promedio = replace_na(Contrabando_casos_promedio, 0)
  )
