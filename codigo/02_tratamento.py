"""
02_tratamento.py — Dos dados brutos aos dados tratados.

Entrada  (dados/brutos/):
  p2fsp_siconfi_dca.tsv(.gz)   Siconfi/STN — DCA Anexos I-C, I-D, I-E, 2015-2025
  p2fsp_ibge_sidra.json        IBGE/SIDRA — tabelas 6579, 4709, 1378, 5938, 1737
  p2fsp_imf_weo_fm_jpn.json    FMI — World Economic Outlook e Fiscal Monitor (out/2026), Japão
  japao_soumu/soumu_receitas_locais_FY2016_2024.csv
                               MIC/Japão — White Paper on Local Public Finance (transcrição)
Saída (dados/tratados/):
  deflator_ipca.csv            IPCA médio anual e fator de deflação (base 2025)
  populacao.csv                população oficial e série harmonizada
  municipios_nominal.csv       variáveis fiscais em R$ correntes (formato longo)
  municipios_painel.csv        painel ano × município com valores reais, per capita, % PIB e razões
  japao_painel.csv             indicadores do Japão (governo geral e governos locais)
  verificacoes.txt             conferências de consistência

Uso: python codigo/02_tratamento.py
"""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos"
TRAT = RAIZ / "dados" / "tratados"
TRAT.mkdir(parents=True, exist_ok=True)

ANOS = list(range(2016, 2026))        # período de análise: 10 anos mais recentes completos
ANO_BASE = 2025
MUN = {3550308: "São Paulo", 3509502: "Campinas"}
VERIF: list[str] = []


# ======================================================================
# 1. Siconfi — leitura
# ======================================================================
def ler_siconfi() -> pd.DataFrame:
    arq = BRUTOS / "p2fsp_siconfi_dca.tsv"
    if not arq.exists():
        with gzip.open(BRUTOS / "p2fsp_siconfi_dca.tsv.gz", "rt", encoding="utf-8") as f:
            return pd.read_csv(f, sep="\t")
    return pd.read_csv(arq, sep="\t")


def codigo(conta: str) -> str | None:
    """Extrai o código numérico da natureza (ex.: '1.7.2.1.01.02.00')."""
    m = re.match(r"\s*(\d(?:\.\d+)+)", str(conta))
    return m.group(1) if m else None


def prefixo(cod: str) -> str:
    """Código sem os segmentos finais zerados — usado para relação hierárquica."""
    partes = cod.split(".")
    while partes and set(partes[-1]) == {"0"}:
        partes.pop()
    return ".".join(partes)


def topo(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém apenas as linhas que não descendem de outra linha selecionada
    (evita dupla contagem quando a regra captura conta-mãe e contas-filhas)."""
    pref = [prefixo(c) for c in df["cod"]]
    manter = []
    for i, p in enumerate(pref):
        anc = any(j != i and p != q and p.startswith(q + ".") for j, q in enumerate(pref))
        manter.append(not anc)
    return df[manter]


def soma_regra(bloco: pd.DataFrame, cod_inicio: tuple[str, ...] = (),
               texto: str | None = None, excluir: str | None = None) -> float:
    """Soma as contas que atendem à regra; NaN se nenhuma conta for encontrada."""
    s = bloco
    if cod_inicio:
        s = s[s["cod"].str.startswith(cod_inicio)]
    if texto:
        s = s[s["conta"].str.contains(texto, case=False, regex=True)]
    if excluir:
        s = s[~s["conta"].str.contains(excluir, case=False, regex=True)]
    if s.empty:
        return np.nan
    return float(topo(s)["valor"].sum())


def linha(bloco: pd.DataFrame, cod_exato: str) -> float:
    """Valor de uma conta agregada pelo prefixo hierárquico (ex.: '1.7' = 1.7.0.0...)."""
    s = bloco[bloco["cod"].map(prefixo) == cod_exato]
    return float(s["valor"].iloc[0]) if len(s) else np.nan


# Regras de compatibilização entre as três classificações de receita
# (2015-2017: Portaria 163/2001; 2018-2021: ementário 2018; 2022+: códigos .50)
def receitas(bloco: pd.DataFrame, ano: int) -> dict:
    r = {}
    r["rec_corrente"] = linha(bloco, "1")
    r["rec_capital"] = linha(bloco, "2")
    r["rec_tributaria"] = linha(bloco, "1.1")
    r["rec_contribuicoes"] = linha(bloco, "1.2")
    r["rec_patrimonial"] = linha(bloco, "1.3")
    r["rec_servicos"] = linha(bloco, "1.6")
    r["transf_correntes"] = linha(bloco, "1.7")
    r["outras_rec_correntes"] = linha(bloco, "1.9")
    r["operacoes_credito"] = linha(bloco, "2.1")
    r["transf_capital"] = linha(bloco, "2.4")
    r["rec_intra"] = np.nansum([linha(bloco, "7"), linha(bloco, "8")]) \
        if not (np.isnan(linha(bloco, "7")) and np.isnan(linha(bloco, "8"))) else np.nan

    imp = ("1.1",)
    r["iptu"] = soma_regra(bloco, imp, r"Propriedade Predial|IPTU")
    r["iss"] = soma_regra(bloco, imp, r"Servi[çc]os de Qualquer Natureza|ISSQN")
    r["itbi"] = soma_regra(bloco, imp, r"Transmiss[ãa]o .?Inter Vivos")
    r["irrf"] = soma_regra(bloco, imp, r"Renda|Retido nas Fontes",
                           excluir=r"Patrim[ôo]nio e a Renda$|Patrim[ôo]nio e a Renda\b")
    r["taxas"] = linha(bloco, "1.1.2")

    if ano <= 2017:
        uniao, estados = ("1.7.2.1", "1.7.6.1"), ("1.7.2.2", "1.7.6.2")
        fundeb = ("1.7.2.4",)
        # Multas, juros e dívida ativa de tributos ficavam em "Outras Receitas Correntes"
        acess = [linha(bloco, "1.9.1.1"), linha(bloco, "1.9.1.3"), linha(bloco, "1.9.3.1")]
        r["trib_acessorios_fora_1_1"] = float(np.nansum(acess))
    else:
        uniao, estados = ("1.7.1",), ("1.7.2",)
        fundeb = ("1.7.5",)
        r["trib_acessorios_fora_1_1"] = 0.0
    r["transf_uniao"] = soma_regra(bloco, uniao)
    r["transf_estado"] = soma_regra(bloco, estados)
    r["fundeb"] = soma_regra(bloco, fundeb, r"Manuten[çc][ãa]o e Desenvolvimento",
                             excluir=r"Complementa")
    r["fpm"] = soma_regra(bloco, ("1.7",), r"Fundo de Participa[çc][ãa]o (?:dos|do) Munic")
    r["icms_cota"] = soma_regra(bloco, ("1.7",), r"Cota-Parte do ICMS")
    r["ipva_cota"] = soma_regra(bloco, ("1.7",), r"Cota-Parte do IPVA")
    r["sus"] = soma_regra(bloco, ("1.7",), r"Sistema [ÚU]nico de Sa[úu]de|SUS",
                          excluir=r"Conv[êe]nio")
    return r


def despesas(bloco_d: pd.DataFrame, bloco_e: pd.DataFrame) -> dict:
    r = {}
    tot = bloco_d[bloco_d["cod_conta"] == "TotalDespesas"]
    r["desp_total"] = float(tot["valor"].iloc[0]) if len(tot) else np.nan
    for nome, c in [("desp_corrente", "3"), ("desp_pessoal", "3.1"), ("desp_juros", "3.2"),
                    ("desp_outras_correntes", "3.3"), ("desp_capital", "4"),
                    ("desp_investimentos", "4.4"), ("desp_inversoes", "4.5"),
                    ("desp_amortizacao", "4.6")]:
        r[nome] = linha(bloco_d, c)
    # Por função (Anexo I-E): só as linhas de função (sem subfunções)
    fun = bloco_e[bloco_e["conta"].str.match(r"^\d\d - ")]
    exc = bloco_e[bloco_e["conta"].str.contains(r"Exceto Intra", case=False)]
    r["desp_exceto_intra"] = float(exc["valor"].iloc[0]) if len(exc) else np.nan
    for nome, c in [("desp_saude", "10"), ("desp_educacao", "12"),
                    ("desp_assistencia", "08"), ("desp_previdencia", "09"),
                    ("desp_urbanismo", "15"), ("desp_transporte", "26")]:
        s = fun[fun["conta"].str.startswith(c + " - ")]
        r[nome] = float(s["valor"].iloc[0]) if len(s) else np.nan
    return r


import warnings
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)


def montar_municipios(dca: pd.DataFrame) -> pd.DataFrame:
    dca = dca.copy()
    dca["cod"] = dca["conta"].map(codigo).fillna("")
    linhas = []
    for (ano, ibge), g in dca.groupby(["exercicio", "cod_ibge"]):
        rc = g[(g.anexo == "DCA-Anexo I-C")]
        bruta = rc[rc.coluna == "Receitas Brutas Realizadas"]
        ded_f = rc[rc.coluna == "Deduções - FUNDEB"]
        ded_o = rc[rc.coluna == "Outras Deduções da Receita"]
        d = g[(g.anexo == "DCA-Anexo I-D") & (g.coluna == "Despesas Empenhadas")]
        e = g[(g.anexo == "DCA-Anexo I-E") & (g.coluna == "Despesas Empenhadas")]
        reg = {"ano": ano, "cod_ibge": ibge, "municipio": MUN[ibge],
               "pop_siconfi": g["populacao"].dropna().iloc[0] if g["populacao"].notna().any() else np.nan}
        reg.update(receitas(bruta, ano))
        reg["deducoes_fundeb"] = linha(ded_f, "1") if len(ded_f) else np.nan
        reg["outras_deducoes"] = linha(ded_o, "1") if len(ded_o) else np.nan
        reg.update(despesas(d, e))
        linhas.append(reg)
    df = pd.DataFrame(linhas).sort_values(["municipio", "ano"])
    return df


# ======================================================================
# 2. IBGE — IPCA, população e PIB
# ======================================================================
def ler_sidra():
    S = json.load(open(BRUTOS / "p2fsp_ibge_sidra.json", encoding="utf-8"))
    tab = {k: pd.DataFrame(v[1:]) for k, v in S.items()}
    return tab


def deflator(tab) -> pd.DataFrame:
    ip = tab["ipca_indice"].copy()
    ip["ano"] = ip["D3C"].str[:4].astype(int)
    ip["indice"] = ip["V"].astype(float)
    anual = ip[ip.ano.between(2015, 2025)].groupby("ano")["indice"].mean().rename("ipca_indice_medio")
    dez = ip[ip["D3C"].str.endswith("12")].set_index("ano")["indice"]
    out = anual.to_frame()
    out["ipca_var_anual_pct"] = (dez / dez.shift(1) - 1).reindex(out.index) * 100
    out["fator_real_base2025"] = out.loc[ANO_BASE, "ipca_indice_medio"] / out["ipca_indice_medio"]
    return out.reset_index()


def populacao(tab) -> pd.DataFrame:
    """Série oficial (estimativas TCU/IBGE) e série harmonizada ao Censo 2022.

    As estimativas 2016-2021 foram projetadas a partir do Censo 2010 e ficaram acima da
    contagem do Censo 2022 (São Paulo: 12,40 mi em 2021 vs 11,45 mi em 2022). Para evitar
    uma quebra artificial nos indicadores per capita, a série harmonizada interpola
    geometricamente entre os Censos 2010 e 2022 (2016-2021) e entre o Censo 2022 e a
    estimativa de 2024 (2023, ano sem estimativa publicada).
    """
    est = tab["pop_estimativas"].copy()
    est["ano"] = est["D3N"].astype(int)
    est["cod_ibge"] = est["D1C"].astype(int)
    est["pop_estimativa_ibge"] = est["V"].astype(float)
    c22 = tab["pop_censo2022"].assign(cod_ibge=lambda x: x.D1C.astype(int),
                                      v=lambda x: x.V.astype(float)).set_index("cod_ibge")["v"]
    c10 = tab["pop_censo2010"].assign(cod_ibge=lambda x: x.D1C.astype(int),
                                      v=lambda x: x.V.astype(float)).set_index("cod_ibge")["v"]
    linhas = []
    for cod in MUN:
        e = est[est.cod_ibge == cod].set_index("ano")["pop_estimativa_ibge"]
        for ano in ANOS:
            oficial = e.get(ano, np.nan)
            fonte = "Estimativa IBGE (SIDRA 6579)"
            if ano == 2022:
                oficial, fonte = c22[cod], "Censo 2022 (SIDRA 4709)"
            if ano <= 2021:
                harm = c10[cod] * (c22[cod] / c10[cod]) ** ((ano - 2010) / 12)
                metodo = "Interpolação geométrica Censo 2010–Censo 2022"
            elif ano == 2022:
                harm, metodo = c22[cod], "Censo 2022"
            elif ano == 2023:
                harm = c22[cod] * (e[2024] / c22[cod]) ** 0.5
                metodo = "Interpolação geométrica Censo 2022–Estimativa 2024"
                fonte = "Sem estimativa publicada para 2023"
            else:
                harm, metodo = oficial, "Estimativa IBGE"
            linhas.append({"ano": ano, "cod_ibge": cod, "municipio": MUN[cod],
                           "pop_oficial": oficial, "fonte_pop_oficial": fonte,
                           "pop_harmonizada": round(harm), "metodo_harmonizacao": metodo})
    return pd.DataFrame(linhas)


def pib(tab) -> pd.DataFrame:
    p = tab["pib_municipal"]
    p = p[p["D2C"] == "37"].copy()      # PIB a preços correntes (mil R$)
    p["ano"] = p["D3N"].astype(int)
    p["cod_ibge"] = p["D1C"].astype(int)
    p["pib_mil_reais"] = pd.to_numeric(p["V"], errors="coerce")
    return p[["ano", "cod_ibge", "pib_mil_reais"]]


# ======================================================================
# 3. Japão
# ======================================================================
def japao() -> pd.DataFrame:
    imf = json.load(open(BRUTOS / "p2fsp_imf_weo_fm_jpn.json", encoding="utf-8"))
    rot = {"GGXWDG_NGDP": "divida_bruta_gg_pct_pib", "GGXWDN_G01_GDP_PT": "divida_liquida_gg_pct_pib",
           "GGR_G01_GDP_PT": "receita_gg_pct_pib", "G_X_G01_GDP_PT": "despesa_gg_pct_pib",
           "GGXCNL_NGDP": "resultado_nominal_gg_pct_pib", "GGXONLB_G01_GDP_PT": "resultado_primario_gg_pct_pib",
           "NGDPD": "pib_bi_usd", "NGDP_RPCH": "pib_cresc_real_pct",
           "PCPIPCH": "inflacao_pct", "LP": "populacao_milhoes"}
    df = pd.DataFrame({rot[k]: pd.Series({int(a): v for a, v in (vals or {}).items()})
                       for k, vals in imf["values"].items() if k in rot})
    df.index.name = "ano"
    df = df.loc[2016:2025].reset_index()
    df["fonte_gg"] = "FMI, World Economic Outlook e Fiscal Monitor, out/2026 (DataMapper API)"
    # O WEO/FM de out/2026 trata 2025 como estimativa (dado ainda não consolidado)
    df["status_fmi"] = np.where(df.ano >= 2025, "estimativa FMI", "observado")

    loc = pd.read_csv(BRUTOS / "japao_soumu" / "soumu_receitas_locais_FY2016_2024.csv")
    loc = loc.rename(columns={"ano_fiscal": "ano"})
    tot = loc["receita_total_tri_iene"]
    loc["jp_transf_total"] = (loc["imposto_local_transferido"] + loc["subvencoes_especiais"]
                              + loc["local_allocation_tax"] + loc["repasses_tesouro_nacional"])
    loc["jp_dep_transf"] = loc["jp_transf_total"] / tot
    loc["jp_dep_transf_incondicional"] = (loc["local_allocation_tax"] + loc["imposto_local_transferido"]
                                          + loc["subvencoes_especiais"]) / tot
    loc["jp_dep_transf_condicional"] = loc["repasses_tesouro_nacional"] / tot
    loc["jp_autonomia_tributaria"] = loc["impostos_locais"] / tot
    loc["jp_endividamento"] = loc["titulos_locais_total"] / tot
    loc = loc.add_prefix("loc_").rename(columns={"loc_ano": "ano"})
    out = df.merge(loc, on="ano", how="left")
    return out


# ======================================================================
# 4. Painel municipal tratado
# ======================================================================
MONET = None  # preenchido em main


def main():
    dca = ler_siconfi()
    nom = montar_municipios(dca)
    nom.to_csv(TRAT / "municipios_nominal.csv", index=False)

    tab = ler_sidra()
    defl = deflator(tab)
    defl.to_csv(TRAT / "deflator_ipca.csv", index=False)
    pop = populacao(tab)
    pop.to_csv(TRAT / "populacao.csv", index=False)
    pb = pib(tab)

    p = nom[nom.ano.isin(ANOS)].merge(defl[["ano", "fator_real_base2025"]], on="ano", how="left")
    p = p.merge(pop[["ano", "cod_ibge", "pop_oficial", "pop_harmonizada"]], on=["ano", "cod_ibge"], how="left")
    p = p.merge(pb, on=["ano", "cod_ibge"], how="left")

    # Agregados derivados (R$ correntes)
    p["rec_exceto_intra"] = p["rec_corrente"] + p["rec_capital"]
    p["rec_corrente_liquida_fundeb"] = p["rec_corrente"] - p["deducoes_fundeb"]
    p["rec_tributaria_harmonizada"] = p["rec_tributaria"] + p["trib_acessorios_fora_1_1"]
    p["transf_total"] = p["transf_correntes"] + p["transf_capital"]
    p["transf_incondicionais"] = p[["fpm", "icms_cota", "ipva_cota"]].sum(axis=1, min_count=3)
    p["transf_condicionadas"] = p[["sus", "fundeb"]].sum(axis=1, min_count=2)
    p["arrecadacao_propria"] = p["rec_tributaria_harmonizada"]
    p["resultado_orcamentario"] = (p["rec_exceto_intra"] + p["rec_intra"].fillna(0)) - p["desp_total"]

    monet = ["rec_corrente", "rec_capital", "rec_exceto_intra", "rec_tributaria", "rec_tributaria_harmonizada",
             "arrecadacao_propria",
             "iptu", "iss", "itbi", "irrf", "taxas", "transf_correntes", "transf_capital", "transf_total",
             "transf_uniao", "transf_estado", "fpm", "icms_cota", "ipva_cota", "sus", "fundeb",
             "transf_incondicionais", "transf_condicionadas", "deducoes_fundeb", "rec_corrente_liquida_fundeb",
             "operacoes_credito", "rec_intra", "desp_total", "desp_exceto_intra", "desp_corrente",
             "desp_pessoal", "desp_juros", "desp_investimentos", "desp_amortizacao", "desp_saude",
             "desp_educacao", "resultado_orcamentario"]
    for v in monet:
        p[f"{v}_real"] = p[v] * p["fator_real_base2025"]
        p[f"{v}_pc_real"] = p[f"{v}_real"] / p["pop_harmonizada"]
    # % do PIB municipal (PIB só até 2023: anos sem PIB ficam NA, não zero)
    for v in ["rec_exceto_intra", "arrecadacao_propria", "transf_total", "desp_exceto_intra"]:
        p[f"{v}_pct_pib"] = p[v] / (p["pib_mil_reais"] * 1000) * 100
    p["pib_pc_real"] = p["pib_mil_reais"] * 1000 * p["fator_real_base2025"] / p["pop_harmonizada"]

    # Razões de dependência e autonomia (sobre receita exceto intraorçamentária)
    p["dep_transf"] = p["transf_total"] / p["rec_exceto_intra"]
    p["dep_transf_correntes"] = p["transf_correntes"] / p["rec_corrente"]
    p["dep_transf_uniao"] = p["transf_uniao"] / p["rec_exceto_intra"]
    p["dep_transf_estado"] = p["transf_estado"] / p["rec_exceto_intra"]
    p["autonomia_tributaria"] = p["arrecadacao_propria"] / p["rec_exceto_intra"]
    p["peso_iss"] = p["iss"] / p["rec_tributaria_harmonizada"]
    p["peso_iptu"] = p["iptu"] / p["rec_tributaria_harmonizada"]
    p["pessoal_sobre_rc"] = p["desp_pessoal"] / p["rec_corrente"]
    p["invest_sobre_desp"] = p["desp_investimentos"] / p["desp_total"]
    p["saude_sobre_desp"] = p["desp_saude"] / p["desp_exceto_intra"]
    p["educ_sobre_desp"] = p["desp_educacao"] / p["desp_exceto_intra"]
    p["quebra_classificacao"] = np.select([p.ano <= 2017, p.ano <= 2021],
                                          ["Portaria 163/2001 (até 2017)", "Ementário 2018-2021"],
                                          "Ementário 2022+")
    p = p.sort_values(["municipio", "ano"])
    p.to_csv(TRAT / "municipios_painel.csv", index=False)

    jp = japao()
    jp.to_csv(TRAT / "japao_painel.csv", index=False)

    # ---------------- verificações
    VERIF.append("VERIFICAÇÕES DE CONSISTÊNCIA\n")
    chk = nom.copy()
    chk["soma_rc"] = chk[["rec_tributaria", "rec_contribuicoes", "rec_patrimonial", "rec_servicos",
                          "transf_correntes", "outras_rec_correntes"]].sum(axis=1)
    chk["dif_rc_pct"] = (chk["rec_corrente"] - chk["soma_rc"]) / chk["rec_corrente"] * 100
    VERIF.append("Receita corrente menos soma das origens principais (% — restante = agropecuária/industrial):")
    VERIF.append(chk[["municipio", "ano", "dif_rc_pct"]].round(2).to_string(index=False))
    falt = p[["municipio", "ano"] + monet].melt(id_vars=["municipio", "ano"])
    falt = falt[falt.value.isna()]
    VERIF.append("\nValores ausentes nas variáveis monetárias (mantidos como NA):")
    VERIF.append(falt.groupby("variable")["ano"].apply(lambda s: sorted(set(s))).to_string() if len(falt) else "nenhum")
    (TRAT / "verificacoes.txt").write_text("\n".join(VERIF), encoding="utf-8")
    print("\n".join(VERIF))
    print("\nArquivos gerados em dados/tratados/")


if __name__ == "__main__":
    main()
