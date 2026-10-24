# P2 — Finanças do Setor Público (CCA0169/UnB, 2026.2)

**Matrícula:** 262031630
**Unidades:** São Paulo/SP, Campinas/SP e Japão
**Período:** 2016–2025. No Japão, os dados dos governos locais vão do ano fiscal 2016 ao 2024.
**Artigo:** [`artigo/262031630_artigo_P2_FSP.pdf`](artigo/262031630_artigo_P2_FSP.pdf)

**Trabalho anterior (ponto de partida):** FREIRE, A. C. T. *Prova 1 — Finanças do Setor Público*, repositório `anaclaratavares89/FSP_PROVA_1`. A cópia integral está em `dados/originais/`. O que foi reaproveitado, corrigido e ampliado está em [`documentacao/registro_alteracoes.md`](documentacao/registro_alteracoes.md).

---

## Organização do repositório

```
├── artigo/
│   ├── 262031630_artigo_P2_FSP.pdf     artigo final (PDF)
│   ├── artigo.html                     fonte do artigo (gera o PDF)
│   └── refs/                           base das referências (metadados OpenAlex)
├── dados/
│   ├── originais/      base do trabalho anterior, sem alterações
│   ├── brutos/         dados coletados diretamente nas fontes oficiais
│   └── tratados/       dados usados nas análises (CSV editáveis)
├── codigo/
│   ├── 01_coleta.py    refaz as consultas às APIs oficiais (Siconfi, IBGE, FMI)
│   ├── 02_tratamento.py  brutos → tratados (compatibilização, deflação, per capita, razões)
│   └── 03_analise.py   tabelas, figuras, regressões e comparação com o trabalho anterior
├── bibliometria/
│   ├── estrategia_busca.md   consulta, base, filtros e critérios
│   ├── 01_filtrar_corpus.py  limpeza do corpus (exclusões documentadas)
│   ├── 02_bibliometria.R     análise com bibliometrix
│   ├── dados/                corpus bruto e filtrado (OpenAlex)
│   └── saidas/               tabelas e figuras do bibliometrix
├── resultados/
│   ├── tabelas/        tab1 a tab7 (CSV)
│   ├── figuras/        fig1 a fig6 (PNG)
│   └── regressoes.txt  saídas completas dos modelos M1 a M7, com diagnósticos
└── documentacao/
    ├── dicionario_variaveis.md   conceito, fonte, unidade, cobertura e fórmula de cada variável
    └── registro_alteracoes.md    comparação entre o material anterior e a nova versão
```

## Fontes de dados

| Dado | Fonte oficial | Acesso |
|---|---|---|
| Receitas e despesas municipais (DCA, Anexos I-C, I-D e I-E) | Secretaria do Tesouro Nacional, Siconfi | API `apidatalake.tesouro.gov.br/ords/siconfi/tt/dca` |
| População (estimativas e Censos 2010/2022) | IBGE, SIDRA tabelas 6579, 4709 e 1378 | API `apisidra.ibge.gov.br` |
| PIB dos municípios | IBGE, SIDRA tabela 5938 | idem |
| IPCA (número-índice) | IBGE, SIDRA tabela 1737 | idem |
| Japão, governo geral | FMI, *World Economic Outlook* e *Fiscal Monitor* (out/2026) | API `imf.org/external/datamapper/api/v1` |
| Japão, governos locais | Ministry of Internal Affairs and Communications (MIC), *White Paper on Local Public Finance* 2022 e 2026 | PDFs oficiais em `dados/brutos/japao_soumu/` |
| Literatura (bibliometria) | OpenAlex | API `api.openalex.org/works` |

## Como reproduzir

**Requisitos:** Python 3.10 ou superior com `pandas`, `numpy`, `matplotlib`, `statsmodels`, `openpyxl` e `requests`. Para a bibliometria, R 4.3 ou superior com `bibliometrix` (5.x) e `openalexR`.

```bash
pip install pandas numpy matplotlib statsmodels openpyxl requests

# (opcional) recoletar os dados brutos — sobrescreve dados/brutos/
python codigo/01_coleta.py

# dados tratados, tabelas, figuras e regressões
python codigo/02_tratamento.py
python codigo/03_analise.py

# bibliometria
python bibliometria/01_filtrar_corpus.py
Rscript bibliometria/02_bibliometria.R
```

O `biblioshiny()`, interface gráfica do bibliometrix usada em aula, abre a base preparada em `bibliometria/saidas/base_bibliometrix.rds`. No RStudio:

```r
library(bibliometrix)
biblioshiny()   # Data → Load a bibliometrix file → base_bibliometrix.rds
```

Os passos 2 e 3 rodam a partir dos arquivos já versionados em `dados/brutos/`, então os resultados do artigo são reproduzidos exatamente. Uma nova coleta pode trazer valores revisados pelas fontes.

## Principais decisões de tratamento (resumo)

- **Valores reais:** R$ de 2025, deflacionados pelo IPCA médio anual. A fórmula é `real = nominal × IPCA₂₀₂₅ / IPCA_t`.
- **Receita:** sem receitas intraorçamentárias, para evitar dupla contagem.
- **Classificação da receita:** mudou em 2018 e de novo em 2022. As contas foram compatibilizadas pela descrição. Antes de 2018, multas, juros e dívida ativa de tributos estavam fora da receita tributária e foram somados a ela.
- **População:** as estimativas de 2016–2021 superestimam a contagem do Censo 2022. O per capita usa uma série harmonizada, e a população oficial entra como teste de sensibilidade.
- **Dados ausentes:** nunca são substituídos por zero. O PIB municipal de 2024–2025 ainda não foi publicado e fica ausente.
