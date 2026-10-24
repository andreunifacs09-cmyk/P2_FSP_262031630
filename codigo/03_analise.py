"""
03_analise.py — Estatísticas descritivas, gráficos, regressões e comparação com o trabalho anterior.

Entrada: dados/tratados/*.csv e dados/originais/*.xlsx
Saída:   resultados/tabelas/*.csv  |  resultados/figuras/*.png  |  resultados/regressoes.txt

Uso: python codigo/03_analise.py
Requer: pandas, numpy, matplotlib, statsmodels, openpyxl
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson, jarque_bera

RAIZ = Path(__file__).resolve().parents[1]
TRAT = RAIZ / "dados" / "tratados"
ORIG = RAIZ / "dados" / "originais"
TAB = RAIZ / "resultados" / "tabelas"
FIG = RAIZ / "resultados" / "figuras"
TAB.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

p = pd.read_csv(TRAT / "municipios_painel.csv")
jp = pd.read_csv(TRAT / "japao_painel.csv")
COR = {"São Paulo": "#1f4e79", "Campinas": "#c55a11", "Japão (governos locais)": "#548235"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight"})
FONTE = "Fonte: elaboração própria com dados do Siconfi/STN e IBGE. Valores em R$ de 2025 (IPCA médio anual)."


def salvar_fig(nome, fonte=FONTE):
    # A fonte de cada figura é informada na legenda do artigo (artigo/gerar_artigo.py)
    plt.savefig(FIG / nome)
    plt.close()


# ======================================================================
# 1. Estatísticas descritivas
# ======================================================================
desc_vars = {
    "rec_exceto_intra_pc_real": "Receita orçamentária per capita (R$ 2025)",
    "arrecadacao_propria_pc_real": "Arrecadação tributária própria per capita (R$ 2025)",
    "transf_total_pc_real": "Transferências intergovernamentais per capita (R$ 2025)",
    "desp_exceto_intra_pc_real": "Despesa empenhada per capita (R$ 2025)",
    "pib_pc_real": "PIB per capita (R$ 2025)",
    "dep_transf": "Dependência de transferências (proporção da receita)",
    "autonomia_tributaria": "Autonomia tributária (proporção da receita)",
    "pessoal_sobre_rc": "Pessoal / receita corrente",
    "invest_sobre_desp": "Investimentos / despesa total",
}
linhas = []
for mun, g in p.groupby("municipio"):
    for v, rot in desc_vars.items():
        s = g[v].dropna()
        cagr = (s.iloc[-1] / s.iloc[0]) ** (1 / (len(s) - 1)) - 1 if v.endswith("_real") else np.nan
        linhas.append({"municipio": mun, "variavel": rot, "n": len(s), "media": s.mean(),
                       "desvio_padrao": s.std(), "minimo": s.min(), "maximo": s.max(),
                       "primeiro_ano": int(g.loc[s.index[0], "ano"]), "ultimo_ano": int(g.loc[s.index[-1], "ano"]),
                       "taxa_cresc_media_anual": cagr})
desc = pd.DataFrame(linhas)
desc.to_csv(TAB / "tab1_descritivas.csv", index=False)

# Tabela-resumo por ano (valores reais per capita e razões)
resumo_cols = ["municipio", "ano", "pop_harmonizada", "rec_exceto_intra_pc_real", "arrecadacao_propria_pc_real",
               "transf_total_pc_real", "desp_exceto_intra_pc_real", "dep_transf", "autonomia_tributaria",
               "dep_transf_uniao", "dep_transf_estado", "rec_exceto_intra_pct_pib", "resultado_orcamentario_real"]
p[resumo_cols].to_csv(TAB / "tab2_painel_resumo.csv", index=False)

# Composição das transferências (média do período, % das transferências totais)
comp = []
for mun, g in p.groupby("municipio"):
    tot = g["transf_total"].sum()
    for v, rot in [("icms_cota", "Cota-parte ICMS"), ("ipva_cota", "Cota-parte IPVA"), ("fpm", "FPM"),
                   ("fundeb", "Fundeb"), ("sus", "SUS (União e Estado)"), ("transf_capital", "Transferências de capital")]:
        comp.append({"municipio": mun, "componente": rot, "participacao_pct": g[v].sum() / tot * 100})
pd.DataFrame(comp).to_csv(TAB / "tab3_composicao_transferencias.csv", index=False)

# ======================================================================
# 2. Gráficos
# ======================================================================
# Fig 1 — receita própria x transferências per capita (R$ 2025)
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for a, (mun, g) in zip(ax, p.groupby("municipio", sort=False)):
    a.plot(g.ano, g.arrecadacao_propria_pc_real, marker="o", color=COR[mun], label="Arrecadação própria")
    a.plot(g.ano, g.transf_total_pc_real, marker="s", ls="--", color="#7f7f7f", label="Transferências")
    a.plot(g.ano, g.desp_exceto_intra_pc_real, marker="^", ls=":", color="black", label="Despesa")
    a.set_title(mun)
    a.set_xticks(range(2016, 2026, 2))
    a.axvspan(2017.5, 2018.5, color="#eee", zorder=0)
ax[0].set_ylabel("R$ de 2025 por habitante")
ax[0].legend(frameon=False, fontsize=8)
fig.suptitle("Arrecadação própria, transferências e despesa per capita (2016–2025)", fontsize=11)
salvar_fig("fig1_receita_transf_despesa_pc.png",
           FONTE + " Faixa cinza: mudança de classificação da receita (2018).")

# Fig 2 — dependência de transferências: SP, Campinas, Japão
fig, ax = plt.subplots(figsize=(8, 4))
for mun, g in p.groupby("municipio"):
    ax.plot(g.ano, g.dep_transf * 100, marker="o", color=COR[mun], label=mun)
ax.plot(jp.ano, jp.loc_jp_dep_transf * 100, marker="D", color=COR["Japão (governos locais)"],
        label="Japão — governos locais (agregado)")
ax.plot(jp.ano, jp.loc_jp_dep_transf_incondicional * 100, ls="--", color=COR["Japão (governos locais)"],
        label="Japão — só transferências incondicionais (LAT etc.)")
ax.set_ylabel("% da receita")
ax.set_ylim(0, 50)
ax.legend(frameon=False, fontsize=8)
ax.set_title("Dependência de transferências intergovernamentais", fontsize=11)
salvar_fig("fig2_dependencia_transferencias.png",
           "Fonte: Siconfi/STN; MIC/Japão, White Paper on Local Public Finance 2022 e 2026 (ano fiscal). "
           "Japão inclui Local Allocation Tax, imposto local transferido, subvenções especiais e repasses do Tesouro.")

# Fig 3 — composição da receita tributária (ISS, IPTU, ITBI, IRRF, taxas), % da arrecadação própria
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for a, (mun, g) in zip(ax, p.groupby("municipio", sort=False)):
    base = g["rec_tributaria_harmonizada"]  # inclui multas/juros/dívida ativa até 2017
    partes = {"ISS": g.iss, "IPTU": g.iptu, "ITBI": g.itbi, "IRRF": g.irrf, "Taxas, acessórios e outros": base - g.iss - g.iptu - g.itbi - g.irrf}
    bottom = np.zeros(len(g))
    for (rot, v), c in zip(partes.items(), ["#1f4e79", "#2e75b6", "#9dc3e6", "#c55a11", "#bfbfbf"]):
        a.bar(g.ano, v / base * 100, bottom=bottom, label=rot, color=c, width=0.75)
        bottom += (v / base * 100).values
    a.set_title(mun)
    a.set_xticks(range(2016, 2026, 2))
ax[0].set_ylabel("% da arrecadação própria")
h_, l_ = ax[0].get_legend_handles_labels()
fig.legend(h_, l_, frameon=False, fontsize=8, ncol=5, loc="lower center", bbox_to_anchor=(0.5, -0.06))
fig.suptitle("Composição da arrecadação tributária própria", fontsize=11)
salvar_fig("fig3_composicao_tributaria.png",
           FONTE.replace(" Valores em R$ de 2025 (IPCA médio anual).", "") +
           " Até 2017, multas, juros e dívida ativa estavam fora da receita tributária.")

# Fig 4 — Japão: governo geral (FMI)
fig, ax1 = plt.subplots(figsize=(8, 3.8))
ax1.bar(jp.ano, jp.resultado_nominal_gg_pct_pib, color=np.where(jp.ano >= 2025, "#c9c9c9", "#9dc3e6"),
        label="Resultado nominal (% PIB, eixo esq.)")
ax1.set_ylabel("Resultado nominal, % do PIB")
ax2 = ax1.twinx()
ax2.plot(jp.ano, jp.divida_bruta_gg_pct_pib, marker="o", color="#1f4e79", label="Dívida bruta (% PIB, eixo dir.)")
ax2.set_ylabel("Dívida bruta, % do PIB")
ax2.spines["right"].set_visible(True)
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="lower left")
ax1.set_title("Japão: dívida bruta e resultado do governo geral", fontsize=11)
salvar_fig("fig4_japao_governo_geral.png",
           "Fonte: FMI, World Economic Outlook e Fiscal Monitor (out/2026). 2025 = estimativa do FMI (barra cinza).")

# Fig 5 — Japão: composição da receita local
cols = [("loc_impostos_locais", "Impostos locais", "#1f4e79"),
        ("loc_local_allocation_tax", "Local Allocation Tax", "#548235"),
        ("loc_repasses_tesouro_nacional", "Repasses do Tesouro (condicionados)", "#a9d18e"),
        ("loc_titulos_locais_total", "Títulos locais", "#c55a11"),
        ("loc_outras_receitas", "Outras (inclui transf. menores)", "#bfbfbf")]
j9 = jp.dropna(subset=["loc_receita_total_tri_iene"]).copy()
j9["loc_outras_receitas"] = j9["loc_outras_receitas"] + j9["loc_imposto_local_transferido"] + j9["loc_subvencoes_especiais"]
fig, ax = plt.subplots(figsize=(8, 3.8))
bottom = np.zeros(len(j9))
for c, rot, cor in cols:
    v = j9[c] / j9["loc_receita_total_tri_iene"] * 100
    ax.bar(j9.ano, v, bottom=bottom, color=cor, label=rot, width=0.75)
    bottom += v.values
ax.set_ylabel("% da receita líquida total")
ax.legend(frameon=False, fontsize=8, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.38))
ax.set_title("Japão: composição da receita dos governos locais (anos fiscais)", fontsize=11)
salvar_fig("fig5_japao_receita_local.png",
           "Fonte: MIC/Japão, White Paper on Local Public Finance 2022 e 2026. Ano fiscal de abril a março.")

# ======================================================================
# 3. Regressões (painel curto: 2 municípios)
# ======================================================================
out = []


def diag(res, nome, X):
    bp = het_breuschpagan(res.resid, res.model.exog)
    jb = jarque_bera(res.resid)
    vif = {X.columns[i]: float(variance_inflation_factor(X.values, i)) for i in range(X.shape[1]) if X.columns[i] not in ("const", "Intercept")}
    return (f"Diagnósticos [{nome}]: n={int(res.nobs)}; R²={res.rsquared:.3f}; R² aj.={res.rsquared_adj:.3f}; "
            f"Breusch-Pagan p={bp[1]:.3f}; Durbin-Watson={durbin_watson(res.resid):.2f}; "
            f"Jarque-Bera p={jb[1]:.3f}; VIF={ {k: round(v, 1) for k, v in vif.items()} }")


def rodar(formula, dados, nome, teste=None):
    res = smf.ols(formula, data=dados).fit(cov_type="HC1")
    X = pd.DataFrame(res.model.exog, columns=res.model.exog_names)
    out.append("=" * 100)
    out.append(f"{nome}\nEquação: {formula}  |  Erros-padrão robustos HC1")
    out.append(res.summary().tables[1].as_text())
    out.append(diag(res, nome, X))
    if teste:
        w = res.wald_test(teste, scalar=True)
        out.append(f"Teste de Wald ({teste}): estatística={float(w.statistic):.3f}; p-valor={float(w.pvalue):.3f}")
    return res


d = p.copy()
d["SP"] = (d.municipio == "São Paulo").astype(int)
d["t"] = d.ano - 2016
# variáveis em R$ mil de 2025 per capita (coeficientes = R$ de despesa por R$ de receita)
for v in ["desp_exceto_intra_pc_real", "transf_total_pc_real", "arrecadacao_propria_pc_real", "pib_pc_real",
          "transf_incondicionais_pc_real", "transf_condicionadas_pc_real", "rec_exceto_intra_pc_real"]:
    if v in d:
        d[v.replace("_pc_real", "")] = d[v] / 1000

d["transf_incond"] = d["transf_incondicionais_pc_real"] / 1000
d["transf_cond"] = d["transf_condicionadas_pc_real"] / 1000
d["desp"] = d["desp_exceto_intra_pc_real"] / 1000
d["transf"] = d["transf_total_pc_real"] / 1000
d["propria"] = d["arrecadacao_propria_pc_real"] / 1000
d["pib"] = d["pib_pc_real"] / 1000
dp = d.dropna(subset=["pib"])

out.append("REGRESSÕES — P2 FSP (262031630). Variáveis em R$ mil de 2025 por habitante, exceto PIB per capita "
           "(R$ mil de 2025). Painel de 2 municípios: inferência limitada; ver texto.")
m1 = rodar("desp ~ transf + pib + SP", dp, "M1 — Flypaper clássico (2016–2023): despesa ~ transferências + PIB per capita + efeito fixo",
           teste="transf = pib")
m2 = rodar("desp ~ transf + propria + SP + t", d, "M2 — Propensão a gastar (2016–2025): despesa ~ transferências + arrecadação própria + tendência",
           teste="transf = propria")
m3 = rodar("propria ~ transf + pib + SP", dp, "M3 — Esforço fiscal (2016–2023): arrecadação própria ~ transferências + PIB per capita")
m4 = rodar("desp ~ transf_incond + transf_cond + propria + SP + t", d,
           "M4 — Tipo de transferência (2016–2025): incondicionais (ICMS, IPVA, FPM) vs condicionadas (SUS, Fundeb)",
           teste="transf_incond = transf_cond")

# Robustez: log-log e primeiras diferenças
d["ln_desp"], d["ln_transf"], d["ln_propria"] = np.log(d.desp), np.log(d.transf), np.log(d.propria)
m5 = rodar("ln_desp ~ ln_transf + ln_propria + SP + t", d, "M5 — Robustez log-log (elasticidades), 2016–2025",
           teste="ln_transf = ln_propria")
fd = d.sort_values(["municipio", "ano"]).copy()
for v in ["desp", "transf", "propria"]:
    fd["d_" + v] = fd.groupby("municipio")[v].diff()
fd = fd.dropna(subset=["d_desp"])
m6 = rodar("d_desp ~ d_transf + d_propria", fd, "M6 — Robustez em primeiras diferenças, 2017–2025",
           teste="d_transf = d_propria")

# Sensibilidade: população oficial (estimativas IBGE) em vez da harmonizada
ds = d.copy()
for v, base in [("desp", "desp_exceto_intra_real"), ("transf", "transf_total_real"), ("propria", "arrecadacao_propria_real")]:
    ds[v] = ds[base] / ds["pop_oficial"] / 1000
ds = ds.dropna(subset=["desp", "transf", "propria"])
m7 = rodar("desp ~ transf + propria + SP + t", ds, "M7 — Sensibilidade: M2 com população oficial (estimativas IBGE; 2023 ausente)",
           teste="transf = propria")

# Japão: correlação entre dependência e autonomia (descritivo, 9 anos fiscais)
jj = jp.dropna(subset=["loc_jp_dep_transf"])
out.append("=" * 100)
out.append("Japão (FY2016–FY2024, n=9) — correlações de Pearson (descritivas, sem inferência causal):")
for a, b in [("loc_jp_autonomia_tributaria", "loc_jp_dep_transf"),
             ("loc_jp_dep_transf_incondicional", "loc_jp_autonomia_tributaria"),
             ("loc_jp_dep_transf", "despesa_gg_pct_pib")]:
    r = jj[[a, b]].corr().iloc[0, 1]
    out.append(f"  corr({a}, {b}) = {r:.3f}")

(RAIZ / "resultados" / "regressoes.txt").write_text("\n".join(out), encoding="utf-8")

# Tabela compacta de coeficientes
def linha_coef(res, nome):
    reg = {"modelo": nome, "n": int(res.nobs), "r2": res.rsquared}
    for k in res.params.index:
        reg[k] = f"{res.params[k]:.3f}{'***' if res.pvalues[k] < .01 else '**' if res.pvalues[k] < .05 else '*' if res.pvalues[k] < .1 else ''} ({res.bse[k]:.3f})"
    return reg
pd.DataFrame([linha_coef(m, n) for m, n in [(m1, "M1"), (m2, "M2"), (m3, "M3"), (m4, "M4"), (m5, "M5"), (m6, "M6"), (m7, "M7")]]) \
    .to_csv(TAB / "tab4_regressoes.csv", index=False)

# Fig 6 — dispersão despesa x transferências
fig, ax = plt.subplots(figsize=(6.5, 4))
for mun, g in d.groupby("municipio"):
    ax.scatter(g.transf * 1000, g.desp * 1000, color=COR[mun], label=mun)
    for _, r in g.iterrows():
        ax.annotate(str(r.ano)[2:], (r.transf * 1000, r.desp * 1000), fontsize=7, xytext=(3, 2), textcoords="offset points")
ax.set_xlabel("Transferências per capita (R$ de 2025)")
ax.set_ylabel("Despesa per capita (R$ de 2025)")
ax.legend(frameon=False)
ax.set_title("Despesa e transferências per capita, 2016–2025", fontsize=11)
salvar_fig("fig6_dispersao_despesa_transf.png")

# ======================================================================
# 4. Comparação com o trabalho anterior
# ======================================================================
q4 = {}
for aba, mun in [("São Paulo", "São Paulo"), ("Campinas", "Campinas")]:
    o = pd.read_excel(ORIG / "Questão 4. Receitas_Despesas_São Paulo_Campina_2016_2025(1).xlsx", sheet_name=aba, header=2)
    o = o.iloc[:, :7]
    o.columns = ["ano", "rec_nom_ant", "desp_nom_ant", "ipca_ant", "rec_real_ant", "desp_real_ant", "saldo_real_ant"]
    o = o[pd.to_numeric(o.ano, errors="coerce").notna()].astype(float)
    o["municipio"] = mun
    q4[mun] = o
ant = pd.concat(q4.values())
ant["ano"] = ant.ano.astype(int)
nov = p[["municipio", "ano", "rec_exceto_intra", "rec_intra", "desp_total", "fator_real_base2025"]].copy()
nov["rec_total_nova"] = nov.rec_exceto_intra + nov.rec_intra
cmp_ = ant.merge(nov, on=["municipio", "ano"])
cmp_["dif_rec_nominal"] = cmp_.rec_total_nova - cmp_.rec_nom_ant
cmp_["rec_real_correta"] = cmp_.rec_total_nova * cmp_.fator_real_base2025
cmp_["desp_real_correta"] = cmp_.desp_total * cmp_.fator_real_base2025
cmp_["erro_rec_real_pct"] = (cmp_.rec_real_ant / cmp_.rec_real_correta - 1) * 100
cmp_ = cmp_[["municipio", "ano", "rec_nom_ant", "rec_total_nova", "dif_rec_nominal", "rec_real_ant",
             "rec_real_correta", "erro_rec_real_pct", "desp_real_ant", "desp_real_correta"]]
cmp_.to_csv(TAB / "tab5_comparacao_trabalho_anterior.csv", index=False)

cres = []
for mun, g in cmp_.groupby("municipio"):
    g = g.sort_values("ano")
    cres.append({"municipio": mun,
                 "cresc_real_receita_anterior_pct": (g.rec_real_ant.iloc[-1] / g.rec_real_ant.iloc[0] - 1) * 100,
                 "cresc_real_receita_corrigido_pct": (g.rec_real_correta.iloc[-1] / g.rec_real_correta.iloc[0] - 1) * 100})
pd.DataFrame(cres).to_csv(TAB / "tab6_crescimento_real_antes_depois.csv", index=False)

# Japão: dívida — fonte anterior x FMI
o2 = pd.read_excel(ORIG / "Questão 2. Japão (2016-2025).xlsx", header=0).iloc[:10, :2]
o2.columns = ["ano", "divida_trading_economics"]
o2["ano"] = o2.ano.astype(int)
o2 = o2.merge(jp[["ano", "divida_bruta_gg_pct_pib", "status_fmi"]], on="ano")
o2["diferenca_pp"] = o2.divida_trading_economics - o2.divida_bruta_gg_pct_pib
o2.to_csv(TAB / "tab7_japao_divida_antes_depois.csv", index=False)

print("\n".join(out))
print("\nTabelas e figuras geradas.")
