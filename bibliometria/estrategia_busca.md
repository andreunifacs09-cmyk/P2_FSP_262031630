# Estratégia de busca bibliométrica

**Objetivo:** mapear a literatura científica sobre transferências intergovernamentais, efeito flypaper e ilusão fiscal em governos locais, para fundamentar o referencial teórico e selecionar as referências do artigo.

## Bases
- Scopus (acesso pelo Portal de Periódicos CAPES, via CAFe/UnB)
- Web of Science Core Collection (idem), opcional, para ampliar a cobertura

## String — Scopus (campo TITLE-ABS-KEY)

```
TITLE-ABS-KEY ( ( "flypaper effect" OR "fiscal illusion" OR "intergovernmental transfer*"
  OR "intergovernmental grant*" OR "fiscal transfer*" OR "equali?ation transfer*"
  OR "revenue sharing" OR "fiscal equali?ation" )
  AND ( municipal* OR "local government*" OR subnational OR "sub-national" OR decentrali?ation ) )
AND ( LIMIT-TO ( DOCTYPE , "ar" ) OR LIMIT-TO ( DOCTYPE , "re" ) )
AND ( LIMIT-TO ( SRCTYPE , "j" ) )
```

Exportar: **Export → BibTeX → marcar todas as informações** (citation, bibliographical, abstract & keywords, funding, other). Salvar como `bibliometria/scopus.bib`.

Se a busca retornar mais de 2.000 documentos, a Scopus exporta em lotes; exporte por intervalos de ano e junte os arquivos (ou restrinja a `PUBYEAR > 1979`).

## String — Web of Science (campo TS)

```
TS=( ("flypaper effect" OR "fiscal illusion" OR "intergovernmental transfer*"
  OR "intergovernmental grant*" OR "fiscal transfer*" OR "equali?ation transfer*"
  OR "revenue sharing" OR "fiscal equali?ation")
  AND (municipal* OR "local government*" OR subnational OR "sub-national" OR decentrali?ation) )
```
Refinar: Document Types = Article, Review Article. Exportar: **Plain text file → Full Record and Cited References** (lotes de 500). Salvar como `bibliometria/wos.txt`.

## Registro (preencher no dia da busca)
| Base | Data | Nº de documentos | Observação |
|---|---|---|---|
| Scopus | | | |
| Web of Science | | | |

## Processamento
`bibliometria/bibliometria.R` (bibliometrix): fusão e remoção de duplicatas, produção anual, Lei de Bradford, documentos mais citados, coocorrência de palavras-chave e mapa temático. A interface `biblioshiny()` gera as mesmas análises de forma interativa.

## Critério de seleção das referências do artigo
Das referências recuperadas, entram no artigo os artigos de periódicos que (i) tratam diretamente de efeito flypaper, ilusão fiscal, dependência de transferências ou esforço fiscal local; (ii) estão entre os mais citados da base ou são recentes (2015+) com evidência empírica; (iii) cobrem Brasil, Japão ou comparações internacionais. Cada referência usada é citada e discutida no texto.
