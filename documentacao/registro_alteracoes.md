# Registro de alterações em relação ao trabalho anterior

**Trabalho anterior:** FREIRE, Ana Clara Tavares. *Prova 1 — Finanças do Setor Público* (São Paulo/SP, Campinas/SP e Japão). Repositório GitHub `anaclaratavares89/FSP_PROVA_1`. Cópia integral preservada em `dados/originais/` (commit registrado em `ORIGEM_commit.txt`).

**Materiais reaproveitados:** a escolha das unidades (São Paulo, Campinas e Japão), o recorte inicial 2016–2025 e a identificação das fontes (Siconfi/STN, IBGE, IPCA). Nenhum valor numérico do trabalho anterior foi reutilizado sem nova coleta na fonte oficial.

## 1. Problemas identificados na base original

| # | Arquivo / local | Problema | Tratamento na nova versão |
|---|---|---|---|
| 1 | Questão 4, colunas "Receita Real" e "Despesa Real" | Deflação feita dividindo o valor nominal por (1 + IPCA do próprio ano). Isso não converte os valores para um ano-base comum: cada ano fica em preços diferentes, e as comparações temporais e o "crescimento real" ficam incorretos. | Deflação por número-índice acumulado do IPCA (média anual), base 2025 = 100: `Valor real = Valor nominal × (Índice 2025 / Índice t)`. |
| 2 | Campinas, Receita Total 2018 | Valor divergente entre planilhas: R$ 5.037.426.435,36 (Questão 3) e R$ 5.073.426.435,36 (Questão 4), dígitos trocados. | Valor recoletado no Siconfi (DCA Anexo I-C). |
| 3 | São Paulo, Receitas Intraorçamentárias 2018 | Registrado como texto "0.00" (e "-" na composição), em ano em que o município arrecadou mais de R$ 1,9 bilhão nessa rubrica em 2016–2017 e 2019. Indica dado ausente tratado como zero. | Recoletado na fonte: o valor existe (R$ 2,07 bi) e foi incorporado. |
| 4 | Questão 2 (Japão) | Fonte não oficial (Trading Economics) e valor de 2025 com duas casas decimais (232,35), sem indicar se é estimativa. | Substituído pelo FMI, *World Economic Outlook* (indicador GGXWDG_NGDP), com metadados verificáveis e identificação de anos estimados. |
| 5 | Questão 3 | Não informa se os valores são receitas brutas ou líquidas de deduções (Fundeb, transferências constitucionais), o que muda a composição; mistura de valores com e sem centavos sugere fontes/extrações diferentes por ano. | Receitas recoletadas com a separação entre receita bruta e deduções; documentada a regra adotada. |
| 6 | Questões 3 e 4 | Valores apenas nominais (Q3) e sem população: impossível comparar municípios de escalas diferentes. | Inclusão de população (IBGE) e de indicadores per capita e em proporção do PIB municipal. |
| 7 | Questão 5 | Série com 7 observações (falta 2022–2023); correlação positiva (+0,85) entre gasto em educação (% PIB) e analfabetismo foi interpretada como se o gasto reduzisse o analfabetismo. Ambas as séries têm tendência; a associação é espúria e o sinal contradiz a interpretação. | Análise não reaproveitada. A nova estratégia empírica trata de transferências e arrecadação própria (tema da P2), com cuidado para tendências e sem interpretação causal. |
| 8 | Geral | Ausência de transferências intergovernamentais detalhadas (FPM, ICMS, IPVA, SUS, Fundeb), centrais para o tema flypaper/ilusão fiscal. | Coletadas a partir do DCA Anexo I-C. |

## 2. Resultado das correções (valores conferidos na fonte)

| Item | Trabalho anterior | Nova versão | Fonte da conferência |
|---|---|---|---|
| Receita total de Campinas, 2018 | R$ 5.037.426.435 (Q3) e R$ 5.073.426.435 (Q4) | **R$ 5.137.426.435** | Siconfi, DCA I-C, "Total Receitas" |
| Receitas intraorçamentárias de São Paulo, 2018 | "0.00" | **R$ 2.066.818.696,66** (contas 7.0 + 8.0): R$ 2,034 bi correntes e R$ 0,033 bi de capital | Siconfi, DCA I-C |
| Receita total de São Paulo, 2016 | R$ 49.608.273.637 | R$ 49.646.156.419,82 (inclui R$ 37,9 mi de receitas de capital intraorçamentárias omitidas) | Siconfi, DCA I-C |
| Crescimento real da receita, 2016–2025, São Paulo | ≈ 157% | **64,6%** | `resultados/tabelas/tab6_crescimento_real_antes_depois.csv` |
| Crescimento real da receita, 2016–2025, Campinas | ≈ 156% | **64,3%** | idem |
| Dívida bruta do Japão, 2016–2025 | 231–258% do PIB (Trading Economics) | **202–229% do PIB** (FMI, WEO out/2026), diferença de 20 a 31 p.p. | `resultados/tabelas/tab7_japao_divida_antes_depois.csv` |

A comparação completa, ano a ano, está em `resultados/tabelas/tab5_comparacao_trabalho_anterior.csv`.

## 3. Inclusões

- **Período:** 2016–2025 mantido (dez exercícios mais recentes com DCA completa). 2015 foi coletado como apoio e não entra nas análises.
- **Novas variáveis municipais:** receitas por imposto (IPTU, ISS, ITBI, IRRF, taxas); transferências por origem (União e Estado) e por tipo (FPM, cotas-partes de ICMS e IPVA, SUS, Fundeb, transferências de capital); deduções para o Fundeb; operações de crédito; despesa por natureza (pessoal, juros, investimentos, amortização) e por função (saúde, educação e outras); população oficial e harmonizada; PIB municipal.
- **Indicadores novos:** valores reais (R$ de 2025), per capita, em % do PIB, dependência de transferências, autonomia tributária e participação do ISS e do IPTU.
- **Japão:** além da dívida bruta (agora FMI), resultado nominal e primário, receita, despesa e dívida líquida do governo geral (FMI) e a composição da receita dos governos locais nos anos fiscais 2016–2024 (MIC, *White Paper on Local Public Finance* 2022 e 2026). Os dados locais japoneses vão até o FY2024 porque o White Paper 2026, o mais recente, cobre esse ano.
- **Análises novas:** regressões M1 a M7, com diagnósticos (`resultados/regressoes.txt`), e o estudo bibliométrico (`bibliometria/`).
- **Removido:** a regressão da Questão 5 (educação × analfabetismo), por ser espúria e estar fora do escopo.

## 4. Quebras de série e mudanças de classificação

1. **Ementário da receita, 2018:** a Portaria Interministerial STN/SOF nº 163/2001 foi atualizada e a natureza da receita ganhou nova estrutura de códigos (por exemplo, a receita tributária passou de "1.1 Receita Tributária" para "1.1 Impostos, Taxas e Contribuições de Melhoria"). Multas, juros e dívida ativa dos tributos deixaram de ficar em 1.9 (Outras Receitas Correntes) e passaram a integrar a conta de cada tributo. **Tratamento:** em 2016–2017, as contas 1.9.1.1, 1.9.1.3 e 1.9.3.1 foram somadas à receita tributária (`arrecadacao_propria`).
2. **Transferências, 2018:** antes, 1.7.2.1 (União), 1.7.2.2 (Estados), 1.7.2.4 (Fundeb) e 1.7.6 (convênios). Desde 2018, 1.7.1 (União), 1.7.2 (Estados) e 1.7.5 (outras instituições públicas, Fundeb). **Tratamento:** mapeamento explícito no `02_tratamento.py`.
3. **Códigos ".50" a partir de 2022:** reorganização das contas de nível mais baixo (por exemplo, o IPTU passou de 1.1.1.8.01.1 para 1.1.1.2.50). **Tratamento:** seleção por descrição, com a conta de maior nível que contém o item, para evitar dupla contagem.
4. **Totais da DCA:** até 2018 há só "Total Receitas", que inclui as intraorçamentárias. A partir de 2019, há também "Receitas (exceto intra-orçamentárias)". **Tratamento:** a receita foi calculada como receitas correntes + de capital (exceto intra) em todos os anos.
5. **População:** quebra entre as estimativas de 2016–2021 (base no Censo 2010) e o Censo 2022, e ausência de estimativa em 2023. **Tratamento:** série harmonizada (ver dicionário). A série oficial é usada no teste de sensibilidade M7.
6. **Japão:** a série de dívida do FMI (WEO out/2026) é a vigente. Edições anteriores do WEO e outras fontes podem trazer níveis diferentes por revisões das contas nacionais. 2025 é estimativa do FMI.
