library(readxl)
View(INCAUTACIÓN_ORO_Y_MERCURIO_1)
colnames(INCAUTACIÓN_ORO_Y_MERCURIO_1)
glimpse(INCAUTACIÓN_ORO_Y_MERCURIO_1)
distinct(INCAUTACIÓN_ORO_Y_MERCURIO_1,UNIDAD_MEDIDA)


fecha_limite


# Importamos datos
INCAUTACIÓN_ORO_Y_MERCURIO <- read_excel("Data/INCAUTACIÓN ORO Y MERCURIO (1).xlsx", 
                                            skip = 5)



# Filtramos datos 
INCAUTACIÓN_ORO_Y_MERCURIO_1 <-  INCAUTACIÓN_ORO_Y_MERCURIO |> 
  dplyr::filter(
    FECHA_HECHO >= fecha_limite
  )




# Calcular promedio por municipio
INCAUTACIÓN_ORO_Y_MERCURIO_MIEX <-  INCAUTACIÓN_ORO_Y_MERCURIO_1 |> 
  mutate(
    CANTIDAD = as.numeric(CANTIDAD)
  ) |> 
  group_by(MUNICIPIO,COD_MUNI) |> 
  summarise(
    delitos_incautacion_oro_mercurio_promedio = mean(CANTIDAD[!is.na(CANTIDAD) & CANTIDAD != 0], na.rm = TRUE),
    delitos_incautacion_oro_mercurio_totales = sum(CANTIDAD, na.rm = TRUE),
    .groups = "drop"
  ) |> 
  mutate(
    delitos_incautacion_oro_mercurio_promedio = round(delitos_incautacion_oro_mercurio_promedio,0)
  )


View(INCAUTACIÓN_ORO_Y_MERCURIO_MIEX)
