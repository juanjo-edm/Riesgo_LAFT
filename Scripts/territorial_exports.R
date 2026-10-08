library(openxlsx)
library(dplyr)
library(tidyr)
library(tibble)

path_output <- "Output/tabla_puntaje_global.xlsx"
path_public_output <- "Output/atlas_territorial_publico.xlsx"
path_app_raw <- "App/data/raw/atlas_territorial_publico.xlsx"

niveles_intensidad <- c("Bajo", "Medio", "Alto", "Muy alto")

as_cod_mpio <- function(x) sprintf("%05.0f", as.numeric(x))
as_cod_dpto <- function(x) sprintf("%02.0f", as.numeric(x))

winsorizar_vector <- function(x, probs = c(0.01, 0.99)) {
  x <- as.numeric(x)
  cortes <- quantile(x, probs = probs, na.rm = TRUE, names = FALSE)
  pmin(pmax(x, cortes[1]), cortes[2])
}

normalizar_minmax <- function(x) {
  x <- as.numeric(x)
  rango <- range(x, na.rm = TRUE)

  if (!all(is.finite(rango)) || diff(rango) == 0) {
    return(rep(0, length(x)))
  }

  (x - rango[1]) / diff(rango)
}

calcular_pesos_critic <- function(matriz, metodo_cor = "pearson") {
  matriz_norm <- as.data.frame(lapply(matriz, normalizar_minmax))
  correlaciones <- cor(matriz_norm, use = "pairwise.complete.obs", method = metodo_cor)
  correlaciones[!is.finite(correlaciones)] <- 0
  diag(correlaciones) <- 1

  desviacion <- apply(matriz_norm, 2, sd, na.rm = TRUE)
  desviacion[!is.finite(desviacion)] <- 0
  informacion <- desviacion * rowSums(1 - correlaciones, na.rm = TRUE)

  if (!is.finite(sum(informacion)) || sum(informacion) == 0) {
    return(setNames(rep(1 / ncol(matriz), ncol(matriz)), colnames(matriz)))
  }

  setNames(informacion / sum(informacion), colnames(matriz))
}

read_territorial_sheet <- function(sheet) {
  openxlsx::read.xlsx(path_output, sheet = sheet) |>
    as_tibble() |>
    mutate(
      cod_dpto = as_cod_dpto(cod_dpto),
      cod_mpio = as_cod_mpio(cod_mpio)
    )
}

catalogo_indicadores <- tribble(
  ~dimension_id, ~dimension_label, ~source_id, ~source_label, ~sheet, ~total_col, ~rate_col, ~z_col, ~included_in_index,
  "CONT", "Contrabando y economías ilícitas", "CONT_CONTR", "Contrabando", "CONT", "Contrabando_casos_totales", "tasa_contrabando", "contr_z", TRUE,
  "CONT", "Contrabando y economías ilícitas", "CONT_PIRA", "Piratería terrestre", "CONT", "Pirateria_casos_totales", "tasa_pirateria", "pira_z", TRUE,
  "CONT", "Contrabando y economías ilícitas", "CONT_LAVA", "Procesos por lavado de activos", "CONT", "Lavado_activos_casos_totales", "tasa_lavado_activos", "lava_z", TRUE,
  "CORR", "Corrupción pública", "CORR_PROC", "Procesos por corrupción pública", "CORR", "CORR_CNT_PROC_TOTALES", "tasa_corrupcion", "corrup_z", TRUE,
  "AMBI", "Delitos ambientales", "AMBI_DEL", "Delitos ambientales", "AMBI", "delitos_ambi_totales", "tasa_delitos_amb", "tasa_delitos_amb_z", TRUE,
  "EXTC", "Extorsión y secuestro", "EXTC_EXT", "Extorsión", "EXTC", "delitos_ext_totales", "tasa_extorcion", "tasa_extorcion_z", TRUE,
  "EXTC", "Extorsión y secuestro", "EXTC_SEC", "Secuestro", "EXTC", "delitos_sec_totales", "tasa_secuestro", "tasa_secuestro_z", TRUE,
  "MIEX", "Minería ilegal", "MIEX_MAQ", "Maquinaria intervenida", "MIEX", "delitos_maquinaria_totales", "tasa_maquinarias", "tasa_maquinarias_z", TRUE,
  "MIEX", "Minería ilegal", "MIEX_MIN", "Minas intervenidas", "MIEX", "delitos_minas_totales", "tasa_minas", "tasa_minas_z", TRUE,
  "MIEX", "Minería ilegal", "MIEX_CAP", "Capturas por minería ilegal", "MIEX", "delitos_capturas_totales", "tasa_capturas", "tasa_capturas_z", TRUE,
  "NARC", "Narcotráfico", "NARC_CULT", "Cultivos ilícitos", "NARC", "delitos_cultivo_totales", "tasa_cultivos", "tasa_cultivos_z", TRUE,
  "NARC", "Narcotráfico", "NARC_BASE", "Base de coca", "NARC", "delitos_base_coca_totales", "tasa_base_coca", "tasa_base_coca_z", TRUE,
  "NARC", "Narcotráfico", "NARC_COCA", "Incautaciones de cocaína", "NARC", "delitos_incautaciones_cocaina_totales", "tasa_cocaina", "tasa_cocaina_z", TRUE,
  "NARC", "Narcotráfico", "NARC_MARI", "Incautaciones de marihuana", "NARC", "delitos_incautaciones_marihuana_totales", "tasa_marihuana", "tasa_marihuana_z", TRUE,
  "NARC", "Narcotráfico", "NARC_LAB", "Laboratorios destruidos", "NARC", "delitos_destruccion_laboratorios_totales", "tasa_laboratorios", "tasa_laboratorios_z", TRUE,
  "NARC", "Narcotráfico", "NARC_INSL", "Insumos líquidos", "NARC", "delitos_insumo_liquido_totales", "tasa_insumos_liquidos", "tasa_insumos_liquidos_z", TRUE,
  "NARC", "Narcotráfico", "NARC_INSS", "Insumos sólidos", "NARC", "delitos_insumo_solido_totales", "tasa_insumos_solidos", "tasa_insumos_solidos_z", TRUE,
  "NARC", "Narcotráfico", "NARC_BASU", "Basuco", "NARC", "delitos_incautaciones_basuco_totales", "tasa_basuco", "tasa_basuco_z", TRUE,
  "NARC", "Narcotráfico", "NARC_HERO", "Heroína", "NARC", "delitos_incautaciones_heroina_totales", "tasa_heroina", "tasa_heroina_z", TRUE,
  "NARC", "Narcotráfico", "NARC_PROC", "Procesos por narcotráfico", "NARC", "delitos_fiscalia_narcotrafico_totales", "tasa_fiscalia_narcotrafico", "tasa_fiscalia_narcotrafico_z", TRUE,
  "TFT", "Terrorismo y eventos asociados", "TFT_MAS", "Masacres", "TFT", "tft_masacres_totales", "tasa_tft_masacres", "tasa_tft_masacres_z", TRUE,
  "TFT", "Terrorismo y eventos asociados", "TFT_VIAS", "Afectación de vías", "TFT", "tft_vias_totales", "tasa_tft_vias", "tasa_tft_vias_z", TRUE,
  "TFT", "Terrorismo y eventos asociados", "TFT_MAP", "Minas antipersonal", "TFT", "tft_map_totales", "tasa_tft_map", "tasa_tft_map_z", TRUE,
  "TFT", "Terrorismo y eventos asociados", "TFT_OLEO", "Oleoductos", "TFT", "tft_oleoductos_totales", "tasa_tft_oleoductos", "tasa_tft_oleoductos_z", TRUE,
  "TFT", "Terrorismo y eventos asociados", "TFT_TERR", "Terrorismo", "TFT", "tft_terrorismo_totales", "tasa_tft_terrorismo", "tasa_tft_terrorismo_z", TRUE,
  "TRAT", "Trata y migración irregular", "TRAT_TRATA", "Trata de personas", "TRAT", "trat_totales", "tasa_trata", "tasa_trata_z", TRUE,
  "HURTO", "Hurto", "HURTO_VEH", "Hurto a vehículos", "VCSC", "vcsc_hv_totales", "tasa_vcsc_hv", "tasa_vcsc_hv_z", TRUE,
  "HURTO", "Hurto", "HURTO_PER", "Hurto a personas", "VCSC", "vcsc_hp_totales", "tasa_vcsc_hp", "tasa_vcsc_hp_z", TRUE,
  "HURTO", "Hurto", "HURTO_RES", "Hurto a residencias", "VCSC", "vcsc_hr_totales", "tasa_vcsc_hr", "tasa_vcsc_hr_z", TRUE,
  "HURTO", "Hurto", "HURTO_COM", "Hurto a comercio", "VCSC", "vcsc_hc_totales", "tasa_vcsc_hc", "tasa_vcsc_hc_z", TRUE,
  "HURTO", "Hurto", "HURTO_FIN", "Hurto a entidades financieras", "VCSC", "vcsc_hef_totales", "tasa_vcsc_hef", "tasa_vcsc_hef_z", TRUE,
  "HOMICIDIOS", "Homicidios", "HOMI_HOMI", "Homicidio", "VCSC", "vcsc_homi_totales", "tasa_vcsc_homi", "tasa_vcsc_homi_z", TRUE,
  "VIOLENCIA_SEXUAL", "Violencia sexual", "VSEX_DEL", "Delitos sexuales", "VCSC", "vcsc_dsx_totales", "tasa_vcsc_dsx", "tasa_vcsc_dsx_z", TRUE,
  "ARMAS", "Armas", "ARMAS_INCA", "Incautación de armas de fuego", "VCSC", "vcsc_arm_totales", "tasa_vcsc_arm", "tasa_vcsc_arm_z", TRUE,
  "CAPTURAS", "Capturas", "CAPTURAS_POL", "Capturas Policía Nacional", "VCSC", "vcsc_cap_totales", "tasa_vcsc_cap", "tasa_vcsc_cap_z", TRUE
) |>
  mutate(
    dimension_order = match(
      dimension_id,
      c("CONT", "CORR", "AMBI", "EXTC", "MIEX", "NARC", "TFT", "TRAT", "HURTO", "HOMICIDIOS", "VIOLENCIA_SEXUAL", "ARMAS", "CAPTURAS")
    ),
    source_order = row_number()
  ) |>
  arrange(dimension_order, source_order)

metadata_cols <- c("cod_dpto", "dpto", "cod_mpio", "nom_mpio", "tipo_municipio", "longitud", "latitud", "poblacion_total")

base_territorial <- read_territorial_sheet("CONT") |>
  select(any_of(metadata_cols)) |>
  distinct(cod_mpio, .keep_all = TRUE)

sheet_cache <- lapply(unique(catalogo_indicadores$sheet), read_territorial_sheet)
names(sheet_cache) <- unique(catalogo_indicadores$sheet)

indicadores_municipales <- lapply(seq_len(nrow(catalogo_indicadores)), function(i) {
  row <- catalogo_indicadores[i, ]
  data <- sheet_cache[[row$sheet]]
  faltantes <- setdiff(c(row$total_col, row$rate_col, row$z_col), names(data))

  if (length(faltantes) > 0) {
    stop(sprintf("Faltan columnas para %s: %s", row$source_id, paste(faltantes, collapse = ", ")))
  }

  data |>
    select(any_of(metadata_cols), total = all_of(row$total_col), tasa = all_of(row$rate_col), z_score = all_of(row$z_col)) |>
    mutate(
      dimension_id = row$dimension_id,
      dimension_label = row$dimension_label,
      source_id = row$source_id,
      source_label = row$source_label,
      included_in_index = row$included_in_index,
      total = ifelse(is.na(as.numeric(total)), 0, as.numeric(total)),
      tasa = ifelse(is.na(as.numeric(tasa)), 0, as.numeric(tasa)),
      z_score = ifelse(is.na(as.numeric(z_score)), 0, as.numeric(z_score))
    )
}) |>
  bind_rows() |>
  group_by(source_id) |>
  mutate(
    z_score_winsor = winsorizar_vector(z_score),
    source_score_norm = normalizar_minmax(z_score_winsor),
    source_score = source_score_norm * 100
  ) |>
  ungroup() |>
  select(any_of(metadata_cols), dimension_id, dimension_label, source_id, source_label, total, tasa, z_score, z_score_winsor, source_score_norm, source_score, included_in_index)

validacion_catalogo <- catalogo_indicadores |>
  group_by(dimension_id, dimension_label) |>
  summarise(fuentes = n(), fuentes_incluidas = sum(included_in_index), .groups = "drop")

if (any(validacion_catalogo$fuentes_incluidas == 0)) {
  stop("Hay dimensiones sin fuentes activas.")
}

if (n_distinct(indicadores_municipales$cod_mpio) != 1122) {
  stop("INDICADORES_MUNICIPALES no conserva 1122 municipios.")
}

matriz_dimensiones <- indicadores_municipales |>
  filter(included_in_index) |>
  group_by(cod_mpio, dimension_id) |>
  summarise(dimension_intensidad_raw = mean(z_score, na.rm = TRUE), .groups = "drop") |>
  group_by(dimension_id) |>
  mutate(
    dimension_intensidad = winsorizar_vector(dimension_intensidad_raw),
    dimension_norm = normalizar_minmax(dimension_intensidad)
  ) |>
  ungroup()

matriz_pesos <- matriz_dimensiones |>
  select(cod_mpio, dimension_id, dimension_intensidad) |>
  pivot_wider(names_from = dimension_id, values_from = dimension_intensidad, values_fill = 0) |>
  arrange(cod_mpio)

pesos_critic <- calcular_pesos_critic(matriz_pesos |> select(-cod_mpio))

if (abs(sum(pesos_critic) - 1) > 1e-8) {
  stop("Los pesos CRITIC no suman 1.")
}

pesos_objetivos_territorial <- tibble(
  fecha_calculo = Sys.Date(),
  metodo = "critic_oficial",
  escenario_oficial = TRUE,
  dimension_id = names(pesos_critic),
  peso = as.numeric(pesos_critic),
  peso_pct = 100 * peso,
  formula = "sd(min-max) * suma(1 - correlacion Pearson)"
) |>
  left_join(catalogo_indicadores |> distinct(dimension_id, dimension_label, dimension_order), by = "dimension_id") |>
  arrange(dimension_order) |>
  select(fecha_calculo, metodo, escenario_oficial, dimension_id, dimension_label, peso, peso_pct, formula)

matriz_dimensiones_score <- matriz_dimensiones |>
  left_join(pesos_objetivos_territorial |> select(dimension_id, peso), by = "dimension_id") |>
  mutate(dimension_score = dimension_norm * peso * 100)

dim_intensidad_wide <- matriz_dimensiones_score |>
  select(cod_mpio, dimension_id, dimension_intensidad) |>
  pivot_wider(names_from = dimension_id, values_from = dimension_intensidad, names_glue = "{dimension_id}_INTENSIDAD", values_fill = 0)

dim_score_wide <- matriz_dimensiones_score |>
  select(cod_mpio, dimension_id, dimension_score) |>
  pivot_wider(names_from = dimension_id, values_from = dimension_score, names_glue = "{dimension_id}_SCORE", values_fill = 0)

total_territorial_1 <- base_territorial |>
  left_join(dim_intensidad_wide, by = "cod_mpio") |>
  left_join(dim_score_wide, by = "cod_mpio")

score_cols_territorial <- grep("_SCORE$", names(total_territorial_1), value = TRUE)

total_territorial_2 <- total_territorial_1 |>
  mutate(
    across(all_of(score_cols_territorial), ~ifelse(is.na(.x), 0, as.numeric(.x))),
    INDICE_TERRITORIAL = rowSums(across(all_of(score_cols_territorial)), na.rm = TRUE),
    INDICE_TERRITORIAL_Z = as.numeric(scale(INDICE_TERRITORIAL)),
    INDICE_TERRITORIAL_Z = ifelse(is.finite(INDICE_TERRITORIAL_Z), INDICE_TERRITORIAL_Z, 0),
    METODO_INDICE = "CRITIC sobre dimensiones territoriales con fuentes winsorizadas 1%-99%"
  )

set.seed(123)

km_total_territorial <- kmeans(
  total_territorial_2 |> select(INDICE_TERRITORIAL_Z),
  centers = 4,
  nstart = 50,
  iter.max = 100
)

centroides_total_territorial <- tibble(
  cluster_total = seq_len(4),
  intensidad = as.numeric(km_total_territorial$centers[, 1])
) |>
  arrange(intensidad) |>
  mutate(intensidad_territorial = niveles_intensidad)

total_territorial <- total_territorial_2 |>
  mutate(cluster_total = km_total_territorial$cluster) |>
  left_join(centroides_total_territorial, by = "cluster_total") |>
  arrange(cod_mpio)

construir_total_departamental <- function(tabla_municipal) {
  tabla_depto_1 <- tabla_municipal |>
    group_by(cod_dpto, dpto) |>
    summarise(
      poblacion_total_depto = sum(poblacion_total, na.rm = TRUE),
      municipios_total = n(),
      municipios_bajo = sum(intensidad_territorial == "Bajo", na.rm = TRUE),
      municipios_medio = sum(intensidad_territorial == "Medio", na.rm = TRUE),
      municipios_alto = sum(intensidad_territorial == "Alto", na.rm = TRUE),
      municipios_muy_alto = sum(intensidad_territorial == "Muy alto", na.rm = TRUE),
      pct_municipios_muy_alto = municipios_muy_alto / municipios_total,
      INDICE_TERRITORIAL_DEPTO = weighted.mean(
        INDICE_TERRITORIAL,
        w = ifelse(is.na(poblacion_total) | poblacion_total <= 0, 1, poblacion_total),
        na.rm = TRUE
      ),
      INDICE_TERRITORIAL_PROM_SIMPLE = mean(INDICE_TERRITORIAL, na.rm = TRUE),
      INDICE_TERRITORIAL_MAX = max(INDICE_TERRITORIAL, na.rm = TRUE),
      .groups = "drop"
    ) |>
    mutate(
      INDICE_TERRITORIAL_DEPTO_Z = as.numeric(scale(INDICE_TERRITORIAL_DEPTO)),
      INDICE_TERRITORIAL_DEPTO_Z = ifelse(is.finite(INDICE_TERRITORIAL_DEPTO_Z), INDICE_TERRITORIAL_DEPTO_Z, 0)
    )

  set.seed(123)

  km_depto <- kmeans(
    tabla_depto_1 |> select(INDICE_TERRITORIAL_DEPTO_Z),
    centers = 4,
    nstart = 50,
    iter.max = 100
  )

  centroides_depto <- tibble(
    cluster_depto = seq_len(4),
    intensidad = as.numeric(km_depto$centers[, 1])
  ) |>
    arrange(intensidad) |>
    mutate(intensidad_territorial_depto = niveles_intensidad)

  tabla_depto_1 |>
    mutate(cluster_depto = km_depto$cluster) |>
    left_join(centroides_depto, by = "cluster_depto") |>
    arrange(desc(INDICE_TERRITORIAL_DEPTO))
}

total_territorial_depto <- construir_total_departamental(total_territorial)

validacion_pesos_territorial <- pesos_objetivos_territorial |>
  summarise(metodo = "critic_oficial", suma_pesos = sum(peso), peso_min = min(peso), peso_max = max(peso))

correlaciones_territorial <- matriz_pesos |>
  select(-cod_mpio) |>
  cor(method = "spearman", use = "pairwise.complete.obs") |>
  as.data.frame() |>
  rownames_to_column("dimension_id")

reemplazar_hoja_territorial <- function(wb, sheet, data) {
  if (sheet %in% names(wb)) {
    removeWorksheet(wb, sheet)
  }

  addWorksheet(wb, sheet)
  writeData(wb, sheet = sheet, x = data)
}

reemplazar_hoja_pesos_territorial <- function(wb, sheet = "PESOS_OBJETIVOS_TERRITORIAL") {
  if (sheet %in% names(wb)) {
    removeWorksheet(wb, sheet)
  }

  addWorksheet(wb, sheet)

  fila <- 1
  writeData(wb, sheet = sheet, x = "Pesos CRITIC por dimensión territorial", startRow = fila, startCol = 1)
  fila <- fila + 2
  writeData(wb, sheet = sheet, x = pesos_objetivos_territorial, startRow = fila, startCol = 1)

  fila <- fila + nrow(pesos_objetivos_territorial) + 3
  writeData(wb, sheet = sheet, x = "Validación de pesos", startRow = fila, startCol = 1)
  fila <- fila + 2
  writeData(wb, sheet = sheet, x = validacion_pesos_territorial, startRow = fila, startCol = 1)

  fila <- fila + nrow(validacion_pesos_territorial) + 3
  writeData(wb, sheet = sheet, x = "Correlación Spearman entre dimensiones", startRow = fila, startCol = 1)
  fila <- fila + 2
  writeData(wb, sheet = sheet, x = correlaciones_territorial, startRow = fila, startCol = 1)
}

wb_territorial <- createWorkbook()
reemplazar_hoja_territorial(wb_territorial, "CATALOGO_INDICADORES", catalogo_indicadores)
reemplazar_hoja_territorial(wb_territorial, "INDICADORES_MUNICIPALES", indicadores_municipales)
reemplazar_hoja_territorial(wb_territorial, "TOTAL_TERRITORIAL", total_territorial)
reemplazar_hoja_territorial(wb_territorial, "TOTAL_TERRITORIAL_DEPTO", total_territorial_depto)
reemplazar_hoja_pesos_territorial(wb_territorial)
dir.create(dirname(path_public_output), recursive = TRUE, showWarnings = FALSE)
saveWorkbook(wb_territorial, file = path_public_output, overwrite = TRUE)

dir.create(dirname(path_app_raw), recursive = TRUE, showWarnings = FALSE)
saveWorkbook(wb_territorial, file = path_app_raw, overwrite = TRUE)
