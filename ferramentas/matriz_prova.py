#!/usr/bin/env python3
"""Prova cruzada: cada ordem de plano em cada cena medida, com e sem erro de tamanho.

Responde "o plano passou porque é bom ou porque a cena estava generosa?". Saída:
resultados/mesa-foto/cruzada/matriz.json. Uso: .venv/bin/python ferramentas/matriz_prova.py
Outras cenas: matriz_prova.py nome=cena.json [nome=cena.json ...] --saida arquivo.json [--deitar]
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from real2sim.cena2mjcf import carregar_cena  # noqa: E402
from real2sim.provar import distribuir_vagas, marcar_deitar, provar  # noqa: E402

R = RAIZ / "resultados/mesa-foto"
CENAS = {"codex": RAIZ / "exemplos/mesa-foto/cena.json", "claude": R / "claude/cena.json",
         "robotics-er-2": R / "gemini-robotics-er-2-preview/cena.json", "argon": R / "gemini-4-argon/cena.json"}
PLANOS = {"lata→bola": ["cilindro", "esfera"], "bola→lata": ["esfera", "cilindro"]}  # por tipo de objeto
SAIDA = R / "cruzada/matriz.json"
MODOS = {"medida": (0.0, False), "tamanho ±15%": (0.15, False), "pior caso": (0.15, True)}


def um(args):
    cena_nome, caminho, plano_nome, modo, deitar = args  # tudo vai junto: o filho não vê globais trocados
    cena = carregar_cena(caminho)
    nome = {o["tipo"]: o["nome"] for o in cena["objetos"]}
    passos = [{"pegar": nome[t], "destino": nome["recipiente"]} for t in PLANOS[plano_nome]]
    passos = distribuir_vagas(cena, marcar_deitar(cena, passos) if deitar else passos)
    tam, pior = MODOS[modo]
    r = provar(cena, passos, 20, 0.9, 0, log=lambda *_: None, tamanho=tam, pior_caso=pior)
    return {"cena": cena_nome, "plano": plano_nome, "modo": modo, "completos": r["planos_completos"],
            "taxa": r["taxa"], "aprovado": r["aprovado"],
            "falhas": {p["passo"]["pegar"]: p["falhas"] for p in r["por_passo"] if p["falhas"]}}


if __name__ == "__main__":
    args = sys.argv[1:]
    deitar = "--deitar" in args  # lata alta vai deitada (R2S_INCLINAR = graus, padrão 60)
    args = [a for a in args if a != "--deitar"]
    if "--saida" in args:
        i = args.index("--saida"); SAIDA = Path(args[i + 1]); del args[i:i + 2]
    if args:
        CENAS = {a.split("=", 1)[0]: Path(a.split("=", 1)[1]) for a in args}
    tarefas = [(c, CENAS[c], p, m, deitar) for c in CENAS for p in PLANOS for m in MODOS]
    with ProcessPoolExecutor(8) as ex:
        linhas = list(ex.map(um, tarefas))
    for c in CENAS:
        b = next(o for o in carregar_cena(CENAS[c])["objetos"] if o["tipo"] == "recipiente")["tamanho"]
        print(f"\ncena {c} (bandeja {'×'.join(f'{t * 100:.0f}' for t in b)} cm)")
        for p in PLANOS:
            print(f"  {p:10s}", "  ".join(f"{m}: {x['completos']:2d}/20" for m in MODOS
                                          for x in linhas if x["cena"] == c and x["plano"] == p and x["modo"] == m))
    saida = SAIDA
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n->", saida)
