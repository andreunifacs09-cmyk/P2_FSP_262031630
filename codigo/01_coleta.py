"""
01_coleta.py — Coleta dos dados brutos diretamente nas APIs oficiais.

P2 — Finanças do Setor Público (CCA0169/UnB, 2026.2) — Matrícula 262031630
Unidades: São Paulo/SP (IBGE 3550308), Campinas/SP (IBGE 3509502) e Japão.

Este script refaz exatamente as consultas usadas para gerar os arquivos de dados/brutos/
(coleta original em 23/10/2026) e grava os mesmos formatos:

  p2fsp_siconfi_dca.tsv.gz     Siconfi/STN — DCA Anexos I-C (receitas), I-D (despesa por natureza)
                               e I-E (despesa por função), 2015-2025, todas as colunas
  p2fsp_ibge_sidra.json        IBGE/SIDRA — população (6579, 4709, 1378), PIB municipal (5938)
                               e IPCA (1737)
  p2fsp_imf_weo_fm_jpn.json    FMI — DataMapper API (WEO e Fiscal Monitor, out/2026), Japão

Os dados do Japão sobre governos locais (MIC, White Paper on Local Public Finance) vêm de PDFs
oficiais; ver dados/brutos/japao_soumu/ e a transcrição em soumu_receitas_locais_FY2016_2024.csv.

Observação: as APIs podem revisar valores (ex.: retificação de DCA no Siconfi, nova edição do
WEO). Uma nova coleta pode, portanto, diferir marginalmente dos arquivos versionados.

Uso:  python codigo/01_coleta.py   (sobrescreve os arquivos de dados/brutos/)
Requer: Python 3.10+, requests.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos"
BRUTOS.mkdir(parents=True, exist_ok=True)
MUNICIPIOS = [3550308, 3509502]
ANOS = range(2015, 2026)
S = requests.Session()
S.headers["User-Agent"] = "P2-FSP-UnB-262031630 (pesquisa academica)"


def get_json(url, params=None, tent=4):
    for i in range(tent):
        try:
            r = S.get(url, params=params, timeout=90)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            print(f"  falha ({e}); nova tentativa")
            time.sleep(5 * (i + 1))
    raise RuntimeError(url)


def siconfi():
    url = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
    cols = ["anexo", "exercicio", "cod_ibge", "instituicao", "populacao", "rotulo", "coluna",
            "cod_conta", "conta", "valor"]
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    w.writerow(cols)
    for anexo in ["DCA-Anexo I-C", "DCA-Anexo I-D", "DCA-Anexo I-E"]:
        for m in MUNICIPIOS:
            for ano in ANOS:
                off, n = 0, 0
                while True:
                    js = get_json(url, {"an_exercicio": ano, "id_ente": m, "no_anexo": anexo, "offset": off})
                    for it in js.get("items", []):
                        w.writerow(["" if it.get(c) is None else str(it.get(c)).replace("\t", " ") for c in cols])
                    n += len(js.get("items", []))
                    if not js.get("hasMore"):
                        break
                    off += len(js["items"])
                print(f"  {anexo} {m} {ano}: {n}")
    with gzip.open(BRUTOS / "p2fsp_siconfi_dca.tsv.gz", "wt", encoding="utf-8") as f:
        f.write(buf.getvalue())


def sidra():
    base = "https://apisidra.ibge.gov.br/values"
    urls = {
        "pop_estimativas": "/t/6579/n6/3550308,3509502/v/9324/p/all",
        "pop_censo2022": "/t/4709/n6/3550308,3509502/v/93/p/2022",
        "pop_censo2010": "/t/1378/n6/3550308,3509502/v/93/p/2010/c287/0/c2/0",
        "pib_municipal": "/t/5938/n6/3550308,3509502/v/all/p/all",
        "ipca_indice": "/t/1737/n1/1/v/2266/p/201412-202512",
        "ipca_var": "/t/1737/n1/1/v/63/p/201501-202512",
    }
    out = {k: get_json(base + u) for k, u in urls.items()}
    json.dump(out, open(BRUTOS / "p2fsp_ibge_sidra.json", "w", encoding="utf-8"), ensure_ascii=False)


def fmi():
    base = "https://www.imf.org/external/datamapper/api/v1"
    ind = ["GGXWDG_NGDP", "GGXCNL_NGDP", "NGDP_RPCH", "PCPIPCH", "LP", "NGDPD",
           "GGXONLB_G01_GDP_PT", "GGR_G01_GDP_PT", "G_X_G01_GDP_PT", "GGXWDN_G01_GDP_PT"]
    meta_all = get_json(base + "/indicators")["indicators"]
    vals = {c: get_json(f"{base}/{c}/JPN").get("values", {}).get(c, {}).get("JPN") for c in ind}
    out = {"values": vals, "meta": {c: meta_all.get(c) for c in ind},
           "acesso": dt.datetime.now(dt.timezone.utc).isoformat(), "endpoint": base + "/{indicador}/JPN"}
    json.dump(out, open(BRUTOS / "p2fsp_imf_weo_fm_jpn.json", "w", encoding="utf-8"))


if __name__ == "__main__":
    print("Siconfi..."); siconfi()
    print("IBGE/SIDRA..."); sidra()
    print("FMI..."); fmi()
    print("Coleta concluída.")
