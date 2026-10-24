"""
01_filtrar_corpus.py — Limpeza do corpus bibliográfico do OpenAlex antes do bibliometrix.

Entrada: bibliometria/dados/openalex_corpus.json.gz
         Resultado bruto da consulta à API do OpenAlex, 2.608 artigos de periódicos.
Saída:   bibliometria/dados/openalex_filtrado.json.gz   (lista de obras, formato da API)
         bibliometria/dados/registro_filtragem.csv   (motivo de exclusão de cada obra)

Motivo da limpeza: o termo "revenue sharing" também é usado na literatura de cadeias de
suprimento (contratos entre fabricante e varejista). Essas obras não tratam de finanças
públicas e são excluídas por critérios explícitos e reproduzíveis.
"""
import gzip
import json
import re
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent / "dados"
J = json.load(gzip.open(BASE / "openalex_corpus.json.gz", "rt", encoding="utf-8"))
obras = J["results"]

CAMPOS_EXCLUIDOS = {"Environmental Science", "Engineering", "Decision Sciences", "Computer Science",
                    "Agricultural and Biological Sciences", "Health Professions", "Medicine", "Energy",
                    "Biochemistry, Genetics and Molecular Biology", "Arts and Humanities", "Mathematics"}
TOPICO_EXCLUIDO = re.compile(r"supply chain|inventory|blockchain|smart grid|tourism|oil palm|waste", re.I)
TEXTO_EXCLUIDO = re.compile(r"supply chain|retailer|manufacturer|wholesale price|channel coordination", re.I)
TEXTO_FISCAL = re.compile(r"flypaper|fiscal illusion|intergovernmental|fiscal transfer|equali[sz]ation|"
                          r"revenue sharing|grants?\b|fiscal federalism|decentrali[sz]ation", re.I)


def resumo(w):
    ii = w.get("abstract_inverted_index") or {}
    pos = {p: t for t, ps in ii.items() for p in ps}
    return " ".join(pos[i] for i in sorted(pos))


reg, manter = [], []
for w in obras:
    topico = (w.get("topics") or [{}])[0] if w.get("topics") else {}
    campo = (topico.get("field") or {}).get("display_name")
    nome_topico = topico.get("display_name") or ""
    texto = f"{w.get('title') or ''} {resumo(w)}"
    motivo = None
    if campo in CAMPOS_EXCLUIDOS:
        motivo = f"campo excluído: {campo}"
    elif TOPICO_EXCLUIDO.search(nome_topico):
        motivo = f"tópico excluído: {nome_topico}"
    elif TEXTO_EXCLUIDO.search(texto):
        motivo = "texto de cadeia de suprimentos"
    elif not TEXTO_FISCAL.search(texto):
        motivo = "sem termo fiscal no título/resumo"
    elif not w.get("publication_year") or w["publication_year"] > 2025:
        motivo = "ano 2026 (ano incompleto)"
    reg.append({"id": w["id"], "ano": w.get("publication_year"), "titulo": w.get("title"),
                "campo": campo, "topico": nome_topico, "excluida": motivo is not None, "motivo": motivo})
    if motivo is None:
        manter.append(w)

pd.DataFrame(reg).to_csv(BASE / "registro_filtragem.csv", index=False)
with gzip.open(BASE / "openalex_filtrado.json.gz", "wt", encoding="utf-8") as f:
    json.dump(manter, f)
print(f"Corpus bruto: {len(obras)} | mantidos: {len(manter)}")
print(pd.DataFrame(reg).groupby("motivo", dropna=False).size().sort_values(ascending=False).to_string())
