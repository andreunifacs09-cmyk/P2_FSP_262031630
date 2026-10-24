# ------------------------------------------------------------------------
# Estudo bibliométrico — P2 Finanças do Setor Público (UnB) — 262031630
# Tema: transferências intergovernamentais, efeito flypaper e ilusão fiscal
# Pacotes: bibliometrix (Aria & Cuccurullo, 2017) e openalexR
# ------------------------------------------------------------------------
# Base: OpenAlex (https://api.openalex.org/works), artigos de periódicos.
#   Consulta (title_and_abstract.search):
#   ("flypaper effect" OR "fiscal illusion" OR "intergovernmental transfers" OR
#    "intergovernmental grants" OR "fiscal transfers" OR "equalization transfers" OR
#    "fiscal equalization" OR "revenue sharing") AND (municipal OR municipalities OR
#    "local government" OR "local governments" OR subnational OR decentralization)
#   Filtros: type:article; primary_location.source.type:journal
# Limpeza prévia: bibliometria/01_filtrar_corpus.py (remove literatura de cadeias de
#   suprimento que usa "revenue sharing" e o ano incompleto de 2026).
#
# Uso (diretório de trabalho = raiz do repositório):
#   Rscript bibliometria/02_bibliometria.R
# Interface gráfica (exigida em aula): library(bibliometrix); biblioshiny()
#   -> em biblioshiny, carregue o arquivo bibliometria/saidas/base_bibliometrix.rds
#      ("Load a bibliometrix file").
#
# Para repetir com Scopus/Web of Science, substitua o bloco "Leitura" por:
#   M <- convert2df("bibliometria/scopus.bib", dbsource = "scopus", format = "bibtex")
# ------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(bibliometrix)
  library(jsonlite)
  library(ggplot2)
})

pasta <- "bibliometria"
saida <- file.path(pasta, "saidas")
dir.create(saida, showWarnings = FALSE)
set.seed(262031630)

# Leitura ----------------------------------------------------------------
obras <- fromJSON(gzfile(file.path(pasta, "dados", "openalex_filtrado.json.gz")), simplifyVector = FALSE)
# formato nativo do bibliometrix para listas da API do OpenAlex (dbsource = "openalex_api")
arq_rdata <- file.path(saida, "openalex_lista.RData")
save(obras, file = arq_rdata)
M <- convert2df(arq_rdata, dbsource = "openalex_api")
M <- M[!is.na(M$PY) & M$PY <= 2025, ]
class(M) <- c("bibliometrixDB", "data.frame")
cat("Documentos na base final:", nrow(M), "\n")
saveRDS(M, file.path(saida, "base_bibliometrix.rds"))

# Indicadores gerais -----------------------------------------------------
res <- biblioAnalysis(M, sep = ";")
S <- summary(res, k = 20, pause = FALSE, verbose = FALSE)
capture.output(summary(res, k = 20, pause = FALSE), file = file.path(saida, "resumo_bibliometrico.txt"))
write.csv(S$MainInformationDF, file.path(saida, "informacoes_principais.csv"), row.names = FALSE)
write.csv(S$AnnualProduction, file.path(saida, "producao_anual.csv"), row.names = FALSE)
write.csv(S$MostRelSources, file.path(saida, "fontes_mais_relevantes.csv"), row.names = FALSE)
write.csv(S$MostCitedPapers, file.path(saida, "mais_citados.csv"), row.names = FALSE)
write.csv(S$MostProdCountries, file.path(saida, "paises_mais_produtivos.csv"), row.names = FALSE)
write.csv(S$MostProdAuthors, file.path(saida, "autores_mais_produtivos.csv"), row.names = FALSE)

# Figura B1 — produção científica anual (formato da Figura 1 de Baker et al., 2022)
ap <- as.data.frame(table(M$PY))
names(ap) <- c("ano", "n")
ap$ano <- as.integer(as.character(ap$ano))
ap <- ap[ap$ano >= 1970, ]
g <- ggplot(ap, aes(ano, n)) +
  geom_col(fill = "#1f4e79", width = 0.8) +
  labs(x = NULL, y = "Artigos publicados",
       title = "Produção científica anual sobre transferências intergovernamentais e efeito flypaper",
       caption = "Fonte: OpenAlex (consulta em out/2026), processado com bibliometrix. Artigos de periódicos, 1970–2025.") +
  theme_minimal(base_size = 10) + theme(panel.grid.minor = element_blank(), plot.caption = element_text(hjust = 0))
ggsave(file.path(saida, "figB1_producao_anual.png"), g, width = 8, height = 3.6, dpi = 200)

# Lei de Bradford --------------------------------------------------------
bf <- bradford(M)
write.csv(bf$table, file.path(saida, "bradford.csv"), row.names = FALSE)

# Lei de Lotka (produtividade de autores)
lk <- tryCatch(lotka(M), error = function(e) tryCatch(lotka(res), error = function(e2) NULL))
if (!is.null(lk)) capture.output(print(lk[c("AuthorProd", "Beta", "C", "R2", "p.value")]), file = file.path(saida, "lotka.txt"))

# Rede de coocorrência de palavras-chave ---------------------------------
campo_kw <- if (sum(nchar(M$DE), na.rm = TRUE) > sum(nchar(M$ID), na.rm = TRUE)) "author_keywords" else "keywords"
NetMatrix <- biblioNetwork(M, analysis = "co-occurrences", network = campo_kw, sep = ";")
png(file.path(saida, "figB2_coocorrencia.png"), 2000, 1500, res = 220)
net <- networkPlot(NetMatrix, n = 40, type = "fruchterman", Title = "Coocorrência de palavras-chave",
                   labelsize = 0.9, size.cex = TRUE, remove.isolates = TRUE, verbose = FALSE)
plot(net$graph)
dev.off()
write.csv(net$cluster_res, file.path(saida, "clusters_coocorrencia.csv"), row.names = FALSE)

# Mapa temático ----------------------------------------------------------
tm <- thematicMap(M, field = ifelse(campo_kw == "keywords", "ID", "DE"), n = 300, minfreq = 3,
                  size = 0.5, repel = TRUE)
ggsave(file.path(saida, "figB3_mapa_tematico.png"), tm$map, width = 8, height = 6, dpi = 200)
write.csv(tm$words, file.path(saida, "mapa_tematico_palavras.csv"), row.names = FALSE)

# Acoplamento histórico / citação local -----------------------------------
lc <- tryCatch(localCitations(M, sep = ";"), error = function(e) NULL)
if (!is.null(lc)) write.csv(head(lc$Papers, 30), file.path(saida, "citacoes_locais.csv"), row.names = FALSE)

# Recortes de interesse --------------------------------------------------
txt <- toupper(paste(M$TI, M$AB, M$DE, M$ID))
recortes <- data.frame(
  recorte = c("Flypaper", "Ilusão fiscal", "Brasil", "Japão", "Brasil + flypaper/ilusão"),
  n = c(sum(grepl("FLYPAPER", txt)), sum(grepl("FISCAL ILLUSION", txt)),
        sum(grepl("BRAZIL", txt)), sum(grepl("JAPAN", txt)),
        sum(grepl("BRAZIL", txt) & grepl("FLYPAPER|FISCAL ILLUSION", txt))))
write.csv(recortes, file.path(saida, "recortes_tematicos.csv"), row.names = FALSE)
print(recortes)
cat("Saídas em", saida, "\n")
