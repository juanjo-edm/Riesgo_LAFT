
# K-MEANS (k=3) PARA RIESGO MUNICIPAL (Bajo/Medio/Alto)
# Basado en: Contrabando_casos_promedio, Pirateria_casos_promedio

library(dplyr)
library(tibble)
library(dplyr)
library(ggplot2)

# 1) Preparación de datos (NA -> 0, log1p para asimetría, y estandarización)----
CONT_DF_2 <- CONT_DF_1 %>%
  mutate(
    # Remplazar na por cero
    contr = ifelse(is.na(Contrabando_casos_promedio), 0, Contrabando_casos_promedio),
    pira  = ifelse(is.na(Pirateria_casos_promedio),   0, Pirateria_casos_promedio),

    # z-score para que ambas variables pesen similar
    contr_z = as.numeric(scale(Contrabando_casos_promedio)),
    pira_z  = as.numeric(scale(Pirateria_casos_promedio))
  )

# 2) Matriz para k-means----
CONT_DF_X <- CONT_DF_2 %>% 
  select(contr_z, pira_z)

# (opcional pero útil) Validación mínima: que haya al menos 3 puntos distintos
n_distintos <- nrow(distinct(CONT_DF_X))

if (n_distintos < 3) {
  stop("No hay suficientes puntos distintos (menos de 3) para ejecutar k-means con k=3.")
}

# 3) Ejecutar k-means (k=3)----
set.seed(123)  # reproducible

CONT_km <- kmeans(
  x = CONT_DF_X,
  centers = 3,
  nstart = 50,     # varios arranques para mejor solución
  iter.max = 100   # iteraciones máximas
)

# 4) Asignar cluster a cada municipio-----
count_df_cluster <- CONT_DF_2 %>%
  mutate(cluster = CONT_km$cluster)

# 5) Ordenar clusters por "intensidad" (centroide contr_z + pira_z) y mapear a riesgo----
#    El cluster con menor intensidad => Bajo, luego Medio, luego Alto
centroides <- as_tibble(CONT_km$centers, rownames = "cluster") %>%
  mutate(
    cluster = as.integer(cluster),
    intensidad = contr_z + pira_z
  ) %>%
  arrange(intensidad) %>%
  mutate(riesgo = c("Bajo", "Medio", "Alto"))

# 6) Resultado final: agregar columna de riesgo----
CONT_DF_1_riesgo <- count_df_cluster %>%
  left_join(centroides %>% select(cluster, riesgo, intensidad), by = "cluster") %>%
  # dejar columnas limpias y útiles
  select(
    cod_dpto, dpto, cod_mpio, nom_mpio, tipo_municipio,
    longitud, latitud,
    Contrabando_casos_promedio, Pirateria_casos_promedio,
    cluster, riesgo
  )

# 7) Resúmenes rápidos (para validar)----
cat("\n--- Conteo por riesgo ---\n")
print(CONT_DF_1_riesgo %>% count(riesgo, sort = TRUE))

cat("\n--- Centros (en z-score) por cluster y su riesgo asignado ---\n")
print(centroides)

cat("\n--- Ejemplo: Top 15 municipios por contrabando + piratería (prom) ---\n")
print(
  CONT_DF_1_riesgo %>%
    mutate(total_prom = Contrabando_casos_promedio + Pirateria_casos_promedio) %>%
    arrange(desc(total_prom)) %>%
    select(cod_dpto, dpto, cod_mpio, nom_mpio, Contrabando_casos_promedio, Pirateria_casos_promedio, riesgo) %>%
    slice_head(n = 15)
)

# 8) Grafico----

# 0) Preparar datos: crear variables escaladas (z-score) sin logs
cont_df_plot <- CONT_DF_1_riesgo %>%
  mutate(
    riesgo  = factor(riesgo, levels = c("Bajo","Medio","Alto")),
    cluster = factor(cluster),
    
    # Si hay NA, los llevo a 0 (ajusta si NA significa "sin dato" y no "sin casos")
    contr = ifelse(is.na(Contrabando_casos_promedio), 0, Contrabando_casos_promedio),
    pira  = ifelse(is.na(Pirateria_casos_promedio),   0, Pirateria_casos_promedio),
    
    # z-score (lo mismo que usa k-means si entrenaste con scale)
    contr_z = as.numeric(scale(contr)),
    pira_z  = as.numeric(scale(pira))
  )

# 1) Convex hull por RIESGO (Bajo/Medio/Alto)
#    Si lo quieres por cluster 1/2/3, cambia group_by(riesgo) -> group_by(cluster)
hulls <- cont_df_plot %>%
  group_by(riesgo) %>%
  dplyr::filter(!is.na(contr_z), !is.na(pira_z)) %>%
  dplyr::filter(n() >= 3) %>%                 # chull requiere >= 3 puntos
  slice(chull(contr_z, pira_z)) %>%
  ungroup()

# 2) Centroides (opcional) para marcar con X
centroides <- cont_df_plot %>%
  group_by(riesgo) %>%
  summarise(
    contr_z = mean(contr_z, na.rm = TRUE),
    pira_z  = mean(pira_z,  na.rm = TRUE),
    n = n(),
    .groups = "drop"
  )

# 3) Gráfico: polígonos + puntos (en el espacio escalado del modelo)
ggplot() +
  geom_polygon(
    data = hulls,
    aes(x = contr_z, y = pira_z, fill = riesgo, group = riesgo),
    alpha = 0.25,
    color = NA
  ) +
  geom_point(
    data = cont_df_plot,
    aes(x = contr_z, y = pira_z, color = riesgo),
    alpha = 0.85,
    size = 1.8
  ) +
  geom_point(
    data = centroides,
    aes(x = contr_z, y = pira_z, color = riesgo),
    shape = 4, size = 5, stroke = 1.2
  ) +
  labs(
    title = "Clusters K-means (k=3) con polígonos (convex hull)",
    subtitle = "Ejes en z-score (scale): mismo espacio usado para entrenar el modelo",
    x = "Contrabando (z-score)",
    y = "Piratería (z-score)",
    color = "Riesgo",
    fill  = "Riesgo"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "right")

