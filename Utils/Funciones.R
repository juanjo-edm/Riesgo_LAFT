
# 1) Funcion de normalizacion----
norm_txt <- function(x) {
  x %>%
    str_trim() %>%
    str_to_upper() %>%
    stringi::stri_trans_general("Latin-ASCII") %>%  # quita tildes
    str_replace_all("[[:punct:]]", " ") %>%         # quita puntuación
    str_replace_all("\\s+", " ") %>%                # colapsa espacios
    str_trim()
}
