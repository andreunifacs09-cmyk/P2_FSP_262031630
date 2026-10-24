"""
gerar_artigo.py — Monta o artigo (HTML e PDF) a partir de:
  artigo/texto.html            corpo do texto com marcadores de citação e de figuras/tabelas
  artigo/refs/referencias.json metadados dos artigos citados (OpenAlex)
  artigo/refs/chaves.tsv       chave de citação, autoria ABNT e forma de citação
  resultados/ e bibliometria/saidas/   tabelas e figuras geradas pelos scripts

Marcadores no texto:
  {chave}           citação entre parênteses: (Autor, ano)
  {chave1;chave2}   várias citações entre parênteses
  {n:chave}         citação narrativa: Autor (ano)
  <!--FIG:x-->      figura;  <!--TAB:x--> tabela

Verifica: toda chave citada existe; toda referência listada é citada; número de artigos citados.
Uso: python artigo/gerar_artigo.py   (gera artigo/artigo.html e artigo/262031630_artigo_P2_FSP.pdf)
"""
import base64
import csv
import html
import json
import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ART = RAIZ / "artigo"
REFS = json.load(open(ART / "refs" / "referencias.json", encoding="utf-8"))
CH = list(csv.DictReader(open(ART / "refs" / "chaves.tsv", encoding="utf-8"), delimiter="\t"))
assert len(CH) == len(REFS), (len(CH), len(REFS))
INFO = {}
for c in CH:
    r = REFS[int(c["idx"])]
    INFO[c["chave"]] = {**c, "ref": r}

texto = (ART / "texto.html").read_text(encoding="utf-8")
usadas: list[str] = []


def cit_paren(chaves):
    partes = []
    for k in chaves:
        if k not in INFO:
            raise KeyError(f"chave inexistente: {k}")
        usadas.append(k)
        partes.append(f'{INFO[k]["paren"]}, {INFO[k]["ano"]}')
    return "(" + "; ".join(partes) + ")"


def sub(m):
    s = m.group(1)
    if s.startswith("n:"):
        k = s[2:]
        if k not in INFO:
            raise KeyError(k)
        usadas.append(k)
        return f'{INFO[k]["narr"]} ({INFO[k]["ano"]})'
    return cit_paren([x.strip() for x in s.split(";")])


texto = re.sub(r"\{((?:n:)?[a-z0-9]+(?:;[a-z0-9]+)*)\}", sub, texto)

# ---------------------------------------------------------------- figuras
FIGS = {
    "B1": (RAIZ / "bibliometria/saidas/figB1_producao_anual.png",
           "Produção científica anual sobre transferências intergovernamentais, efeito <em>flypaper</em> e ilusão fiscal (1970–2025)",
           "Elaboração própria com dados do OpenAlex (consulta em out./2026), processados com o pacote bibliometrix. N = 1.636 artigos."),
    "1": (RAIZ / "resultados/figuras/fig1_receita_transf_despesa_pc.png",
          "Arrecadação própria, transferências e despesa per capita — São Paulo e Campinas, 2016–2025 (R$ de 2025)",
          "Elaboração própria com dados do Siconfi/STN e do IBGE. Valores deflacionados pelo IPCA médio anual (base 2025)."),
    "2": (RAIZ / "resultados/figuras/fig2_dependencia_transferencias.png",
          "Dependência de transferências intergovernamentais (% da receita) — São Paulo, Campinas e governos locais do Japão",
          "Elaboração própria com dados do Siconfi/STN e do MIC (2022; 2026). Japão em anos fiscais (abril–março)."),
    "3": (RAIZ / "resultados/figuras/fig3_composicao_tributaria.png",
          "Composição da arrecadação tributária própria — São Paulo e Campinas, 2016–2025 (%)",
          "Elaboração própria com dados do Siconfi/STN. Arrecadação própria compatibilizada: até 2017 inclui multas, juros e dívida ativa de tributos, registrados fora da receita tributária naquele ementário (\"acessórios\")."),
    "5": (RAIZ / "resultados/figuras/fig5_japao_receita_local.png",
          "Japão: composição da receita líquida dos governos locais, anos fiscais 2016–2024 (%)",
          "Elaboração própria com dados do MIC (2022; 2026), <em>White Paper on Local Public Finance</em>."),
    "4": (RAIZ / "resultados/figuras/fig4_japao_governo_geral.png",
          "Japão: dívida bruta e resultado nominal do governo geral, 2016–2025 (% do PIB)",
          "Elaboração própria com dados do FMI (IMF, 2026). 2025: estimativa do FMI."),
    "6": (RAIZ / "resultados/figuras/fig6_dispersao_despesa_transf.png",
          "Despesa e transferências per capita — São Paulo e Campinas, 2016–2025 (R$ de 2025)",
          "Elaboração própria com dados do Siconfi/STN e do IBGE. Rótulos indicam o ano."),
    "A1": (RAIZ / "bibliometria/saidas/figB2_coocorrencia.png",
           "Rede de coocorrência das palavras-chave dos autores (40 termos mais frequentes)",
           "Elaboração própria com dados do OpenAlex, processados com o bibliometrix (algoritmo de Fruchterman-Reingold)."),
    "A2": (RAIZ / "bibliometria/saidas/figB3_mapa_tematico.png",
           "Mapa temático da literatura (centralidade × densidade)",
           "Elaboração própria com dados do OpenAlex, processados com o bibliometrix."),
}
nfig = 0


def fig_html(chave):
    global nfig
    nfig += 1
    arq, tit, fonte = FIGS[chave]
    b64 = base64.b64encode(arq.read_bytes()).decode()
    return (f'<figure><figcaption>Figura {nfig} – {tit}</figcaption>'
            f'<img src="data:image/png;base64,{b64}"><p class="fonte">Fonte: {fonte}</p></figure>')


# ---------------------------------------------------------------- tabelas
def br(x, d=1):
    if pd.isna(x):
        return "–"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


ntab = 0


def caption(tit, quadro=False):
    global ntab
    if quadro:
        return f"<caption>Quadro 1 – {tit}</caption>"
    ntab += 1
    return f"<caption>Tabela {ntab} – {tit}</caption>"


def tab_variaveis():
    linhas = [
        ("Arrecadação própria", "Impostos, taxas e contribuições de melhoria, incluídos multas, juros e dívida ativa (compatibilizado)", "Siconfi, DCA I-C (conta 1.1; 1.9 até 2017)", "R$ de 2025 per capita"),
        ("Transferências", "Transferências correntes (1.7) + de capital (2.4)", "Siconfi, DCA I-C", "R$ de 2025 per capita"),
        ("Incondicionais / condicionadas", "ICMS + IPVA + FPM / SUS + Fundeb", "Siconfi, DCA I-C", "R$ de 2025 per capita"),
        ("Receita", "Receitas correntes + de capital, exceto intraorçamentárias", "Siconfi, DCA I-C", "R$ de 2025 per capita"),
        ("Despesa", "Despesa empenhada, exceto intraorçamentária", "Siconfi, DCA I-E", "R$ de 2025 per capita"),
        ("PIB per capita", "PIB municipal a preços correntes / população", "IBGE, SIDRA 5938", "R$ de 2025 per capita (até 2023)"),
        ("Dependência de transferências", "Transferências / receita", "Calculada", "proporção"),
        ("Autonomia tributária", "Arrecadação própria / receita", "Calculada", "proporção"),
        ("População", "Série harmonizada aos Censos 2010 e 2022 (oficial em sensibilidade)", "IBGE, SIDRA 6579, 4709, 1378", "habitantes"),
        ("Deflator", "IPCA, número-índice médio anual, base 2025", "IBGE, SIDRA 1737", "índice"),
        ("Japão — dependência e autonomia", "Transferências do centro e impostos locais / receita líquida total", "MIC (2022; 2026)", "proporção, ano fiscal"),
        ("Japão — governo geral", "Dívida bruta, resultado nominal e primário, receita e despesa", "FMI, WEO e Fiscal Monitor", "% do PIB"),
    ]
    h = ['<table class="quadro">', caption("Variáveis, definições, fontes e unidades", quadro=True),
         "<tr><th>Variável</th><th>Definição / fórmula</th><th>Fonte</th><th>Unidade</th></tr>"]
    h += [f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in linhas]
    h.append('<tr><td colspan="4" class="fonte">Fonte: elaboração própria. Dicionário completo em <code>documentacao/dicionario_variaveis.md</code>.</td></tr></table>')
    return "\n".join(h)


def tab_antesdepois():
    t = pd.read_csv(RAIZ / "resultados/tabelas/tab5_comparacao_trabalho_anterior.csv")
    g = pd.read_csv(RAIZ / "resultados/tabelas/tab6_crescimento_real_antes_depois.csv")
    t = t[t.ano.isin([2016, 2018, 2021, 2025])]
    h = ['<table>', caption("Receita total: trabalho anterior × versão corrigida (R$ bilhões)"),
         "<tr><th>Município</th><th>Ano</th><th>Nominal anterior</th><th>Nominal (Siconfi)</th>"
         "<th>Real anterior</th><th>Real corrigida (R$ 2025)</th><th>Diferença real (%)</th></tr>"]
    for _, r in t.iterrows():
        h.append(f"<tr><td>{r.municipio}</td><td>{r.ano}</td><td>{br(r.rec_nom_ant/1e9,3)}</td><td>{br(r.rec_total_nova/1e9,3)}</td>"
                 f"<td>{br(r.rec_real_ant/1e9,2)}</td><td>{br(r.rec_real_correta/1e9,2)}</td><td>{br(r.erro_rec_real_pct,1)}</td></tr>")
    for _, r in g.iterrows():
        h.append(f'<tr class="soma"><td colspan="5">Crescimento real 2016–2025 — {r.municipio}: anterior {br(r.cresc_real_receita_anterior_pct,1)}%</td>'
                 f'<td colspan="2">corrigido {br(r.cresc_real_receita_corrigido_pct,1)}%</td></tr>')
    h.append('<tr><td colspan="7" class="fonte">Fonte: elaboração própria com dados de Freire (2026), do Siconfi/STN e do IBGE. '
             'Receita total inclui intraorçamentárias, para comparabilidade com o trabalho anterior. O "real anterior" dividia o valor nominal por (1 + IPCA do ano).</td></tr></table>')
    return "\n".join(h)


def tab_descritivas():
    p = pd.read_csv(RAIZ / "dados/tratados/municipios_painel.csv")
    vs = [("rec_exceto_intra_pc_real", "Receita per capita (R$)", 0, 1),
          ("arrecadacao_propria_pc_real", "Arrecadação própria per capita (R$)", 0, 1),
          ("transf_total_pc_real", "Transferências per capita (R$)", 0, 1),
          ("desp_exceto_intra_pc_real", "Despesa per capita (R$)", 0, 1),
          ("pib_pc_real", "PIB per capita (R$, até 2023)", 0, 1),
          ("dep_transf", "Dependência de transferências (%)", 1, 100),
          ("autonomia_tributaria", "Autonomia tributária (%)", 1, 100),
          ("peso_iss", "ISS / arrecadação própria (%)", 1, 100),
          ("pessoal_sobre_rc", "Pessoal / receita corrente (%)", 1, 100),
          ("invest_sobre_desp", "Investimentos / despesa (%)", 1, 100)]
    h = ['<table>', caption("Estatísticas descritivas — São Paulo e Campinas, 2016–2025 (valores reais de 2025)"),
         '<tr><th rowspan="2">Variável</th><th colspan="4">São Paulo</th><th colspan="4">Campinas</th></tr>'
         "<tr><th>Média</th><th>D.P.</th><th>2016</th><th>2025</th><th>Média</th><th>D.P.</th><th>2016</th><th>2025</th></tr>"]
    for v, rot, d, mult in vs:
        cel = []
        for mun in ["São Paulo", "Campinas"]:
            s = p[p.municipio == mun].set_index("ano")[v] * mult
            ult = s.dropna().index.max()
            cel += [br(s.mean(), d), br(s.std(), d), br(s.get(2016), d), br(s.get(ult), d) + ("*" if ult != 2025 else "")]
        h.append(f"<tr><td>{rot}</td>" + "".join(f"<td>{c}</td>" for c in cel) + "</tr>")
    h.append('<tr><td colspan="9" class="fonte">Fonte: elaboração própria com dados do Siconfi/STN e do IBGE. n = 10 anos por município (8 para o PIB). '
             '* valor de 2023, último disponível. D.P. = desvio-padrão.</td></tr></table>')
    return "\n".join(h)


def tab_composicao():
    c = pd.read_csv(RAIZ / "resultados/tabelas/tab3_composicao_transferencias.csv")
    pv = c.pivot(index="componente", columns="municipio", values="participacao_pct")
    ordem = ["Cota-parte ICMS", "Fundeb", "Cota-parte IPVA", "SUS (União e Estado)", "FPM", "Transferências de capital"]
    h = ['<table>', caption("Composição das transferências recebidas, soma 2016–2025 (% do total de transferências)"),
         "<tr><th>Componente</th><th>São Paulo</th><th>Campinas</th></tr>"]
    for k in ordem:
        h.append(f"<tr><td>{k}</td><td>{br(pv.loc[k,'São Paulo'])}</td><td>{br(pv.loc[k,'Campinas'])}</td></tr>")
    resto = 100 - pv.loc[ordem].sum()
    h.append(f"<tr><td>Demais transferências correntes</td><td>{br(resto['São Paulo'])}</td><td>{br(resto['Campinas'])}</td></tr>")
    h.append('<tr><td colspan="3" class="fonte">Fonte: elaboração própria com dados do Siconfi/STN. Valores brutos (antes da dedução para o Fundeb).</td></tr></table>')
    return "\n".join(h)


def tab_regressoes():
    t = pd.read_csv(RAIZ / "resultados/tabelas/tab4_regressoes.csv").set_index("modelo")
    txt = (RAIZ / "resultados/regressoes.txt").read_text(encoding="utf-8")
    pos = [(m.group(1), m.start()) for m in re.finditer(r"^(M\d) — ", txt, flags=re.M)]
    wald, bp, dw = {}, {}, {}
    for j, (k, ini) in enumerate(pos):
        fim = pos[j + 1][1] if j + 1 < len(pos) else len(txt)
        b = txt[ini:fim]
        w = re.search(r"Teste de Wald.*p-valor=([\d.]+)", b)
        wald[k] = float(w.group(1)) if w else None
        bp[k] = float(re.search(r"Breusch-Pagan p=([\d.]+)", b).group(1))
        dw[k] = float(re.search(r"Durbin-Watson=([\d.]+)", b).group(1))
    linhas = [("transf", "Transferências"), ("transf_incond", "Transf. incondicionais"), ("transf_cond", "Transf. condicionadas"),
              ("propria", "Arrecadação própria"), ("pib", "PIB per capita"), ("ln_transf", "ln Transferências"),
              ("ln_propria", "ln Arrecadação própria"), ("d_transf", "Δ Transferências"), ("d_propria", "Δ Arrecadação própria"),
              ("SP", "D<sup>SP</sup> (São Paulo)"), ("t", "Tendência"), ("Intercept", "Constante")]
    mods = list(t.index)
    dep = {"M1": "Desp", "M2": "Desp", "M3": "Própria", "M4": "Desp", "M5": "ln Desp", "M6": "Δ Desp", "M7": "Desp"}
    h = ['<table class="reg">', caption("Resultados das regressões (MQO, erros-padrão robustos HC1 entre parênteses)"),
         "<tr><th></th>" + "".join(f"<th>{m}</th>" for m in mods) + "</tr>",
         "<tr><td>Variável dependente</td>" + "".join(f"<td>{dep[m]}</td>" for m in mods) + "</tr>"]
    for v, rot in linhas:
        if v not in t.columns:
            continue
        cel = []
        for m in mods:
            x = t.loc[m, v]
            if pd.isna(x):
                cel.append("")
            else:
                coef, se = x.split(" ")
                cel.append(coef.replace(".", ",") + "<br><span class='se'>" + se.replace(".", ",") + "</span>")
        h.append(f"<tr><td>{rot}</td>" + "".join(f"<td>{c}</td>" for c in cel) + "</tr>")
    h.append("<tr class='soma'><td>Observações</td>" + "".join(f"<td>{int(t.loc[m,'n'])}</td>" for m in mods) + "</tr>")
    h.append("<tr><td>R²</td>" + "".join(f"<td>{br(t.loc[m,'r2'],3)}</td>" for m in mods) + "</tr>")
    h.append("<tr><td>Wald: transf. = alternativa (p)</td>" + "".join(f"<td>{('&lt; 0,001' if wald.get(m) is not None and wald.get(m) < 0.001 else br(wald.get(m),3)) if wald.get(m) is not None else '–'}</td>" for m in mods) + "</tr>")
    h.append("<tr><td>Breusch-Pagan (p)</td>" + "".join(f"<td>{br(bp[m],3)}</td>" for m in mods) + "</tr>")
    h.append("<tr><td>Durbin-Watson</td>" + "".join(f"<td>{br(dw[m],2)}</td>" for m in mods) + "</tr>")
    h.append(f'<tr><td colspan="{len(mods)+1}" class="fonte">Fonte: elaboração própria. Variáveis em R$ mil de 2025 por habitante. '
             "*** p &lt; 0,01; ** p &lt; 0,05; * p &lt; 0,1. Wald: M1 transf. = PIB; M2, M7 transf. = própria; M4 incond. = cond.; M5 e M6 em log/diferença. "
             "M1 e M3: 2016–2023 (PIB disponível até 2023); M7 usa população oficial (2023 ausente). Saída completa em <code>resultados/regressoes.txt</code>.</td></tr></table>")
    return "\n".join(h)


TABS = {"variaveis": tab_variaveis, "antesdepois": tab_antesdepois, "descritivas": tab_descritivas,
        "composicao": tab_composicao, "regressoes": tab_regressoes}


def marcador(m):
    tipo, k = m.group(1), m.group(2)
    return fig_html(k) if tipo == "FIG" else TABS[k]()


texto = re.sub(r"<!--(FIG|TAB):(\w+)-->", marcador, texto)

# ---------------------------------------------------------------- referências
def titulo(t):
    t = html.unescape(t or "").strip()
    if t.isupper() or sum(c.isupper() for c in t) > 0.6 * sum(c.isalpha() for c in t):
        t = t.capitalize()
    return t.replace("M exican", "Mexican").replace(" ,", ",")


def periodico(p):
    p = html.unescape(p or "").replace("&amp", "&").replace("& ", "& ")
    return p.replace("Public Budgeting & Finance", "Public Budgeting & Finance")


def abnt(k):
    i = INFO[k]
    r = i["ref"]
    vol = f", v. {r['volume']}" if r.get("volume") else ""
    num = f", n. {r['numero']}" if r.get("numero") else ""
    if r.get("pag_ini") and r.get("pag_fim") and r["pag_ini"] != r["pag_fim"]:
        pag = f", p. {r['pag_ini']}-{r['pag_fim']}"
    elif r.get("pag_ini"):
        pag = f", art. {r['pag_ini']}" if str(r["pag_ini"]).isdigit() and int(str(r["pag_ini"])) > 5000 else f", p. {r['pag_ini']}"
    else:
        pag = ""
    doi = r.get("doi")
    doi_txt = f" DOI: {doi.replace('https://doi.org/', '')}." if doi else ""
    ano = re.sub(r"[ab]$", "", i["ano"])
    return f'{i["autores_abnt"]} {titulo(r["titulo"])}. <em>{periodico(r["periodico"])}</em>{vol}{num}{pag}, {ano}.{doi_txt}'


citadas = sorted(set(usadas), key=lambda k: (INFO[k]["autores_abnt"].lower(), INFO[k]["ano"]))
nao_citadas = sorted(set(INFO) - set(usadas))
if nao_citadas:
    raise SystemExit(f"Referências não citadas no texto: {nao_citadas}")

OFICIAIS = [
    "BRASIL. [Constituição (1988)]. <em>Constituição da República Federativa do Brasil de 1988</em>. Brasília, DF: Presidência da República, 1988.",
    "BRASIL. <em>Emenda Constitucional nº 132, de 20 de dezembro de 2023</em>. Altera o Sistema Tributário Nacional. Brasília, DF: Congresso Nacional, 2023.",
    "FERREIRA, L. O. G. <em>Constitutional tax transfer in Brazilian municipalities: the fiscal illusion and the flypaper effect</em>. 2021. Tese (Doutorado) – Universidade de Brasília, Brasília, 2021.",
    "FREIRE, A. C. T. <em>Prova 1 – Finanças do Setor Público</em> (São Paulo/SP, Campinas/SP e Japão). Brasília: UnB, 2026. Repositório GitHub: anaclaratavares89/FSP_PROVA_1. Disponível em: https://github.com/anaclaratavares89/FSP_PROVA_1. Acesso em: 23 out. 2026.",
    "IBGE – INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. <em>SIDRA: tabelas 6579 (estimativas da população), 4709 (Censo 2022) e 1378 (Censo 2010)</em>. Rio de Janeiro: IBGE, 2026a. Disponível em: https://apisidra.ibge.gov.br. Acesso em: 23 out. 2026.",
    "IBGE – INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. <em>SIDRA: tabela 5938 – Produto interno bruto dos municípios</em>. Rio de Janeiro: IBGE, 2026b. Disponível em: https://apisidra.ibge.gov.br. Acesso em: 23 out. 2026.",
    "IBGE – INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. <em>SIDRA: tabela 1737 – IPCA, série histórica</em>. Rio de Janeiro: IBGE, 2026c. Disponível em: https://apisidra.ibge.gov.br. Acesso em: 23 out. 2026.",
    "IMF – INTERNATIONAL MONETARY FUND. <em>World Economic Outlook and Fiscal Monitor, October 2026</em>: DataMapper API. Washington, DC: IMF, 2026. Disponível em: https://www.imf.org/external/datamapper. Acesso em: 23 out. 2026.",
    "MIC – MINISTRY OF INTERNAL AFFAIRS AND COMMUNICATIONS (Japão). <em>White Paper on Local Public Finance, 2022</em>: illustrated. Tóquio: MIC, 2022. Disponível em: https://www.soumu.go.jp/iken/zaisei/r04data/chihouzaisei_2022_en.pdf. Acesso em: 23 out. 2026.",
    "MIC – MINISTRY OF INTERNAL AFFAIRS AND COMMUNICATIONS (Japão). <em>White Paper on Local Public Finance, 2026</em>: illustrated. Tóquio: MIC, 2026. Disponível em: https://www.soumu.go.jp/iken/zaisei/r08data/chihouzaisei_2026_en.pdf. Acesso em: 23 out. 2026.",
    "OPENALEX. <em>OpenAlex API: works</em>. 2026. Disponível em: https://api.openalex.org/works. Acesso em: 23 out. 2026.",
    "STN – SECRETARIA DO TESOURO NACIONAL. <em>Siconfi: Declaração de Contas Anuais (DCA), Anexos I-C, I-D e I-E – São Paulo/SP e Campinas/SP, 2015–2025</em>. Brasília: STN, 2026. Disponível em: https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca. Acesso em: 23 out. 2026.",
]

refs_html = ['<h2 class="semnum">Referências</h2>', '<h3 class="semnum">Artigos de periódicos científicos</h3>', '<div class="refs">']
refs_html += [f"<p>{abnt(k)}</p>" for k in citadas]
refs_html += ["</div>", '<h3 class="semnum">Documentos oficiais, bases de dados, legislação, tese e trabalho anterior</h3>', '<div class="refs">']
refs_html += [f"<p>{x}</p>" for x in OFICIAIS]
refs_html.append("</div>")

apendice = ['<h2 class="semnum apendice">Apêndice A – Estudo bibliométrico: análises complementares</h2>',
            "<p>A rede de coocorrência (Figura A) usa as palavras-chave dos autores dos 1.636 artigos. O agrupamento principal reúne os termos ligados a "
            "transferências, descentralização e federalismo fiscal, e conecta <em>flypaper effect</em>, <em>fiscal illusion</em>, <em>own-source revenue</em> e "
            "<em>local taxation</em>; um segundo agrupamento, mais genérico, reúne <em>local government</em>, <em>federalism</em>, <em>government spending</em> e "
            "<em>intergovernmental relations</em>. O mapa temático classifica <em>intergovernmental transfers</em> como tema básico (alta centralidade) e "
            "<em>fiscal federalism</em> como tema de nicho bem desenvolvido. A estratégia de busca, os filtros, os registros excluídos e o código estão em "
            "<code>bibliometria/</code> no repositório; a base pode ser carregada no <code>biblioshiny()</code>.</p>",
            fig_html("A1").replace(f"Figura {nfig} –", "Figura A –"),
            fig_html("A2").replace(f"Figura {nfig + 1} –", "Figura B –")]

n_art = len(citadas)
corpo = texto + "\n" + "\n".join(refs_html) + "\n" + "\n".join(apendice)

CSS = (ART / "estilo.css").read_text(encoding="utf-8")
doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Transferências e efeito flypaper — São Paulo, Campinas e Japão</title>
<style>{CSS}</style></head><body>{corpo}</body></html>"""
(ART / "artigo.html").write_text(doc, encoding="utf-8")
print(f"Artigos de periódicos citados: {n_art} | citações no texto: {len(usadas)} | figuras: {nfig} | tabelas: {ntab}")

# ---------------------------------------------------------------- PDF
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.goto((ART / "artigo.html").resolve().as_uri())
    pg.pdf(path=str(ART / "262031630_artigo_P2_FSP.pdf"), format="A4", print_background=True,
           margin={"top": "25mm", "bottom": "22mm", "left": "28mm", "right": "20mm"},
           display_header_footer=True,
           header_template="<div style='font-size:7pt;width:100%;text-align:right;padding-right:20mm;color:#666;font-family:Georgia,serif'>Matrícula 262031630 — P2 Finanças do Setor Público</div>",
           footer_template="<div style='font-size:8pt;width:100%;text-align:center;color:#444;font-family:Georgia,serif'><span class='pageNumber'></span></div>")
    b.close()
print("PDF gerado:", ART / "262031630_artigo_P2_FSP.pdf")
