# Dicionário de variáveis

Arquivos descritos: `dados/tratados/municipios_painel.csv`, `dados/tratados/japao_painel.csv`, `dados/tratados/populacao.csv` e `dados/tratados/deflator_ipca.csv`. O código que gera cada variável está em `codigo/02_tratamento.py`.

## Convenções gerais

- **Período:** 2016–2025, os dez exercícios mais recentes com DCA completa no Siconfi para os dois municípios. 2015 é coletado só como apoio e não entra nas análises.
- **Unidades:** São Paulo/SP (IBGE 3550308) e Campinas/SP (IBGE 3509502), Prefeitura (Poder Executivo consolidado, como declarado no DCA). Japão: governo geral (FMI) e agregado dos governos locais, ou seja, 47 províncias e cerca de 1.700 municípios (MIC).
- **Valores monetários:** R$ correntes no arquivo nominal. Nos arquivos tratados, o sufixo `_real` indica R$ de 2025 e o sufixo `_pc_real` indica R$ de 2025 por habitante.
- **Deflator:** IPCA, número-índice médio anual (IBGE, SIDRA 1737, variável 2266), base 2025 = 1. Fórmula: `valor_real_t = valor_nominal_t × (IPCA_médio_2025 / IPCA_médio_t)`. A média anual foi escolhida porque receitas e despesas são fluxos realizados ao longo do ano.
- **Receita:** "Receitas Brutas Realizadas" do DCA Anexo I-C, sem receitas intraorçamentárias (`rec_exceto_intra`), para evitar dupla contagem de operações entre órgãos do mesmo ente. As deduções para o Fundeb estão em variável própria.
- **Despesa:** despesa empenhada (DCA Anexos I-D e I-E).
- **Dados ausentes:** mantidos como vazio (NA), nunca substituídos por zero. O PIB municipal só existe até 2023, então indicadores em % do PIB e PIB per capita ficam NA em 2024–2025.
- **Quebras de série:** a classificação da receita mudou em 2018 (novo ementário) e de novo a partir de 2022 (novos códigos ".50"). As variáveis foram compatibilizadas pela descrição das contas (ver `quebra_classificacao` e a seção 3 do registro de alterações).

## Municípios: `municipios_painel.csv`

| Variável | Definição | Fonte | Unidade | Transformação / fórmula |
|---|---|---|---|---|
| `ano` | Exercício financeiro | — | ano | — |
| `cod_ibge`, `municipio` | Identificação do município | IBGE | código/texto | — |
| `rec_corrente` | Receitas correntes (cat. 1) | Siconfi, DCA I-C | R$ correntes | Conta 1.0.0.0 |
| `rec_capital` | Receitas de capital (cat. 2) | Siconfi, DCA I-C | R$ | Conta 2.0.0.0 |
| `rec_exceto_intra` | Receita orçamentária total, exceto intraorçamentária | Siconfi, DCA I-C | R$ | `rec_corrente + rec_capital` |
| `rec_intra` | Receitas intraorçamentárias (cat. 7 e 8) | Siconfi, DCA I-C | R$ | Soma das contas 7 e 8 |
| `rec_tributaria` | Impostos, taxas e contribuições de melhoria (conta 1.1), como publicado | Siconfi, DCA I-C | R$ | Conta 1.1 |
| `trib_acessorios_fora_1_1` | Multas, juros e dívida ativa de tributos registrados fora da conta 1.1 (só até 2017) | Siconfi, DCA I-C | R$ | Contas 1.9.1.1 + 1.9.1.3 + 1.9.3.1 (2016–2017). Zero a partir de 2018, porque essas receitas passaram para a conta 1.1 |
| `rec_tributaria_harmonizada` = `arrecadacao_propria` | Arrecadação tributária própria comparável no tempo | Calculada | R$ | `rec_tributaria + trib_acessorios_fora_1_1` |
| `iptu`, `iss`, `itbi`, `irrf` | Principais impostos municipais e IR retido na fonte | Siconfi, DCA I-C | R$ | Conta de maior nível que contém o imposto. Até 2017, sem multas e dívida ativa |
| `taxas` | Taxas (conta 1.1.2) | Siconfi | R$ | — |
| `transf_correntes` | Transferências correntes (conta 1.7) | Siconfi | R$ | — |
| `transf_capital` | Transferências de capital (conta 2.4) | Siconfi | R$ | — |
| `transf_total` | Transferências intergovernamentais totais | Calculada | R$ | `transf_correntes + transf_capital` |
| `transf_uniao` | Transferências correntes da União | Siconfi | R$ | 2016–17: 1.7.2.1 + 1.7.6.1. Desde 2018: 1.7.1 |
| `transf_estado` | Transferências correntes do Estado | Siconfi | R$ | 2016–17: 1.7.2.2 + 1.7.6.2. Desde 2018: 1.7.2 |
| `fpm` | Cota-parte do Fundo de Participação dos Municípios (inclui cotas de 1%) | Siconfi | R$ | Busca por descrição |
| `icms_cota`, `ipva_cota` | Cotas-partes estaduais do ICMS e do IPVA (brutas) | Siconfi | R$ | Busca por descrição |
| `sus` | Transferências fundo a fundo do SUS (União e Estado) | Siconfi | R$ | Busca por descrição, sem convênios |
| `fundeb` | Recursos recebidos do Fundeb, exceto complementação da União | Siconfi | R$ | 2016–17: 1.7.2.4. Desde 2018: 1.7.5 |
| `transf_incondicionais` | ICMS + IPVA + FPM | Calculada | R$ | Soma |
| `transf_condicionadas` | SUS + Fundeb | Calculada | R$ | Soma |
| `deducoes_fundeb` | Dedução da receita corrente para formação do Fundeb | Siconfi, coluna "Deduções – FUNDEB" | R$ | — |
| `operacoes_credito` | Operações de crédito (conta 2.1) | Siconfi | R$ | — |
| `desp_total` | Despesa empenhada total, incluindo intraorçamentária | Siconfi, DCA I-D | R$ | Linha "Total Geral da Despesa" |
| `desp_exceto_intra` | Despesa empenhada, exceto intraorçamentária | Siconfi, DCA I-E | R$ | — |
| `desp_pessoal`, `desp_juros`, `desp_investimentos`, `desp_amortizacao` | Grupos de natureza 3.1, 3.2, 4.4 e 4.6 | Siconfi, DCA I-D | R$ | Incluem a parcela intraorçamentária (modalidade 91) |
| `desp_saude`, `desp_educacao` | Despesa nas funções 10 e 12 | Siconfi, DCA I-E | R$ | — |
| `resultado_orcamentario` | Receita total (com intra) − despesa empenhada total | Calculada | R$ | — |
| `pop_oficial` | População oficial do ano | IBGE: estimativas (SIDRA 6579) e Censo 2022 (SIDRA 4709) | habitantes | 2023: NA (não há estimativa publicada) |
| `pop_harmonizada` | População compatível com o Censo 2022 | Calculada | habitantes | Ver `populacao.csv` |
| `pib_mil_reais` | PIB municipal a preços correntes | IBGE, PIB dos Municípios (SIDRA 5938, v. 37) | R$ mil | Disponível até 2023. 2024–2025 = NA |
| `fator_real_base2025` | Fator de conversão para R$ de 2025 | IBGE, IPCA | adimensional | `IPCA_2025 / IPCA_t` |
| `*_real` | Variável em R$ de 2025 | Calculada | R$ 2025 | `valor × fator_real_base2025` |
| `*_pc_real` | Variável em R$ de 2025 por habitante | Calculada | R$ 2025/hab. | `valor_real / pop_harmonizada` |
| `*_pct_pib` | Variável em % do PIB municipal | Calculada | % | `valor / (pib_mil_reais × 1000) × 100` |
| `pib_pc_real` | PIB per capita em R$ de 2025 | Calculada | R$ 2025/hab. | — |
| `dep_transf` | Dependência de transferências | Calculada | proporção | `transf_total / rec_exceto_intra` |
| `dep_transf_uniao`, `dep_transf_estado` | Dependência por ente transferidor | Calculada | proporção | `/ rec_exceto_intra` |
| `autonomia_tributaria` | Participação da arrecadação própria na receita | Calculada | proporção | `arrecadacao_propria / rec_exceto_intra` |
| `peso_iss`, `peso_iptu` | Participação do ISS e do IPTU na arrecadação própria | Calculada | proporção | — |
| `pessoal_sobre_rc` | Despesa de pessoal / receita corrente bruta | Calculada | proporção | Indicador descritivo, **não** é o limite da LRF, que usa a RCL |
| `invest_sobre_desp` | Investimentos / despesa total | Calculada | proporção | — |
| `quebra_classificacao` | Regime de classificação da receita no ano | — | texto | — |

**Endereços eletrônicos**

- Siconfi (API de dados abertos): `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?an_exercicio={ano}&id_ente={ibge}&no_anexo=DCA-Anexo%20I-C` (idem para I-D e I-E)
- IBGE/SIDRA: `https://apisidra.ibge.gov.br/values/t/{tabela}/n6/3550308,3509502/v/{variável}/p/all`
- IPCA: `https://apisidra.ibge.gov.br/values/t/1737/n1/1/v/2266/p/201412-202512`

## Japão: `japao_painel.csv`

| Variável | Definição | Fonte | Unidade | Observação |
|---|---|---|---|---|
| `divida_bruta_gg_pct_pib` | Dívida bruta do governo geral | FMI, WEO out/2026 (GGXWDG_NGDP) | % do PIB | 2025 = estimativa |
| `divida_liquida_gg_pct_pib` | Dívida líquida do governo geral | FMI, Fiscal Monitor out/2026 | % do PIB | — |
| `receita_gg_pct_pib`, `despesa_gg_pct_pib` | Receita e despesa do governo geral | FMI, Fiscal Monitor | % do PIB | — |
| `resultado_nominal_gg_pct_pib`, `resultado_primario_gg_pct_pib` | Capacidade (+) ou necessidade (−) de financiamento | FMI, WEO e FM | % do PIB | — |
| `pib_cresc_real_pct`, `inflacao_pct`, `populacao_milhoes`, `pib_bi_usd` | Contexto macroeconômico | FMI, WEO | % / milhões / US$ bi | — |
| `loc_receita_total_tri_iene` | Receita líquida total dos governos locais | MIC, *White Paper on Local Public Finance* 2022 e 2026, "Revenue Trends" | ¥ trilhões | Ano fiscal (abr–mar). FY2016–FY2024 |
| `loc_impostos_locais` | Impostos locais | idem | ¥ tri | — |
| `loc_local_allocation_tax` | *Local Allocation Tax* (transferência de equalização, incondicional) | idem | ¥ tri | — |
| `loc_repasses_tesouro_nacional` | *National treasury disbursements* (transferências condicionadas) | idem | ¥ tri | — |
| `loc_imposto_local_transferido`, `loc_subvencoes_especiais` | *Local transfer tax* e *special local grants* | idem | ¥ tri | — |
| `loc_titulos_locais_total` | Emissão de títulos locais (inclui títulos para medidas extraordinárias) | idem | ¥ tri | — |
| `loc_jp_transf_total` | Transferências do governo central | Calculada | ¥ tri | soma de LAT, imposto transferido, subvenções e repasses |
| `loc_jp_dep_transf` | Dependência de transferências | Calculada | proporção | `loc_jp_transf_total / receita total` |
| `loc_jp_dep_transf_incondicional`, `loc_jp_dep_transf_condicional` | Dependência por tipo de transferência | Calculada | proporção | — |
| `loc_jp_autonomia_tributaria` | Impostos locais / receita total | Calculada | proporção | — |

Os dados do MIC foram transcritos dos gráficos "Revenue Trends" (p. 09) dos White Papers 2022 (FY2016–FY2020) e 2026 (FY2020–FY2024), cujos PDFs estão em `dados/brutos/japao_soumu/`. FY2020 aparece nas duas edições com valores idênticos. A soma dos componentes confere com o total em todos os anos, com diferença de até ±0,2 tri por arredondamento.

## `populacao.csv`

As estimativas do IBGE de 2016–2021 foram projetadas a partir do Censo 2010 e ficaram bem acima do Censo 2022. Em São Paulo, a estimativa de 2021 é de 12,40 milhões, contra 11,45 milhões no Censo 2022. Usar essas estimativas criaria uma queda artificial de cerca de 8% na população entre 2021 e 2022, e uma alta correspondente nos indicadores per capita. A série harmonizada (`pop_harmonizada`) é construída assim:

- **2016–2021:** `Censo2010 × (Censo2022/Censo2010)^((t−2010)/12)`, interpolação geométrica.
- **2022:** Censo 2022.
- **2023:** `Censo2022 × (Estimativa2024/Censo2022)^0,5`.
- **2024–2025:** estimativas do IBGE.

A série oficial também é mantida (`pop_oficial`) e usada em teste de sensibilidade (modelo M7).
