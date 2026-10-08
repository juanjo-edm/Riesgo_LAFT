library(httr2)
library(tidyverse)
library(conflicted)
library(tibble)

library(dplyr)
library(stringr)
library(stringi)
library(tibble)

anio_limite

# 1) Cargar datos de filscalia -----

url_procesos_fiscalia_dca <-  "https://www.datos.gov.co/resource/6d52-qyqg.json"


# Delitos DCA de Ley 599 de 2000, Título XV
PROCESOS_FISCALIA_corr <- request(url_procesos_fiscalia_dca) |>
  req_url_query(
    `$query` = glue("
    SELECT *
    WHERE
      criminalidad = 'SI'
      AND es_archivo = 'NO'
      AND es_preclusion = 'NO'
      AND etapa_caso IN ('EJECUCIÓN DE PENAS','TERMINACIÓN ANTICIPADA')

      -- ====== INCLUIR: Delitos contra la administración pública (Título XV) ======
      AND (
        -- PECULADO
        lower(delito) LIKE '%peculad%'

        -- CONCUSIÓN
        OR lower(delito) LIKE '%concusi%'

        -- COHECHO
        OR lower(delito) LIKE '%cohech%'

        -- CELEBRACIÓN INDEBIDA DE CONTRATOS / INTERÉS INDEBIDO / REQUISITOS
        OR lower(delito) LIKE '%celebraci%n indebida de contrato%'
        OR lower(delito) LIKE '%celebración indebida de contrato%'
        OR lower(delito) LIKE '%inter% indebido% celebraci%n% contrato%'
        OR lower(delito) LIKE '%inter% indebido% celebración% contrato%'
        OR lower(delito) LIKE '%contrato sin% requisit%'
        OR lower(delito) LIKE '%incumplimiento% requisit% legal%'

        -- TRÁFICO DE INFLUENCIAS (servidor público y particular)
        OR lower(delito) LIKE '%trafico de influen%'
        OR lower(delito) LIKE '%tráfico de influen%'

        -- ENRIQUECIMIENTO ILÍCITO (servidor público) 
        OR lower(delito) LIKE '%enriquecimiento ilicito%'
        OR lower(delito) LIKE '%enriquecimiento ilícito%'

        -- PREVARICATO
        OR lower(delito) LIKE '%prevaricat%'

        -- ABUSO DE AUTORIDAD / ABUSO DE FUNCIÓN PÚBLICA
        OR lower(delito) LIKE '%abuso de autorid%'
        OR lower(delito) LIKE '%abuso de funci%n p%b%'
        OR lower(delito) LIKE '%abuso de función púb%'

        -- USURPACIÓN / SIMULACIÓN DE INVESTIDURA
        OR lower(delito) LIKE '%usurpaci%n de funci%n%'
        OR lower(delito) LIKE '%usurpación de función%'
        OR lower(delito) LIKE '%simulaci%n de investidura%'
        OR lower(delito) LIKE '%simulación de investidura%'

        -- UTILIZACIÓN INDEBIDA DE INFORMACIÓN (por función pública)
        OR lower(delito) LIKE '%utilizaci%n indebida de informaci%n%'
        OR lower(delito) LIKE '%utilización indebida de información%'
        OR lower(delito) LIKE '%informaci%n obtenida en el ejercicio de funci%n p%b%'
        OR lower(delito) LIKE '%información obtenida en el ejercicio de función púb%'
        OR lower(delito) LIKE '%informaci%n oficial privilegiada%'
        OR lower(delito) LIKE '%información oficial privilegiada%'
      )

      -- ====== EXCLUIR: NO son Título XV (los “colados” típicos) ======
      AND NOT (
        -- Enriquecimiento ilícito de particulares (Art. 327)
        lower(delito) LIKE '%enriquecimiento ilicito de particulares%'
        OR lower(delito) LIKE '%enriquecimiento ilícito de particulares%'
        OR lower(delito) LIKE '%art. 327%'
        OR lower(delito) LIKE '%art 327%'

        -- Información privilegiada (Art. 258) [no confundir con Art. 431]
        OR lower(delito) LIKE '%informacion privilegiada%'
        OR lower(delito) LIKE '%información privilegiada%'
        OR lower(delito) LIKE '%art. 258%'
        OR lower(delito) LIKE '%art 258%'

        -- Contrato de seguro (Art. 172)
        OR lower(delito) LIKE '%contrato de seguro%'
        OR lower(delito) LIKE '%art. 172%'
        OR lower(delito) LIKE '%art 172%'

        -- Concierto para delinquir (Art. 340)
        OR lower(delito) LIKE '%concierto para delinquir%'
        OR lower(delito) LIKE '%art. 340%'
        OR lower(delito) LIKE '%art 340%'
      )
      ---- Filtro de ventana de tiempo
      AND a_o_hechos >= '{anio_limite}'
      
      ---- Indicamos un limit para que no traga mil por defecto
      LIMIT 1000000
    ")
  ) |>
  req_perform() |>
  resp_body_json(simplifyVector = TRUE) |>
  as_tibble()





delitos <- distinct(PROCESOS_FISCALIA_corr,delito) |>  distinct()
dim(PROCESOS_FISCALIA_corr)
