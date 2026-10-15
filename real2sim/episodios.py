"""Uma cena -> muitos episódios de treino (randomização de domínio).

Cada episódio sorteia pequenas variações (posição, giro, massa, atrito dos objetos), roda o
gerador em malha fechada e grava:
  ep_NNNN.npz   série temporal a 50 Hz: juntas, comando, garra, posição do TCP e do objeto, fase
                (+ imagens 128x128 das câmeras 'cima' e 'pulso' a 10 Hz com --imagens)
  ep_NNNN.json  anotação hierárquica em 4 níveis (objetivo > subtarefa > primitiva > eventos) e
                selo de qualidade (o episódio que falhou fica marcado e não entra no treino)
"""
from __future__ import annotations

import copy
import json
import os
import time
from pathlib import Path

import mujoco
import numpy as np

from .cena2mjcf import compilar, validar_cena
from .gerador import Gerador, ir_para_casa

FASES = ["aproximar", "descer", "fechar", "subir", "levar", "baixar", "abrir", "recuar", "assentar"]


GARRA_MAX = 0.078  # abertura útil da garra do Panda (8 cm menos folga)


def variar_tamanho(o: dict, fator: float) -> None:
    """Escala o objeto; o que a garra pega nunca passa da abertura máxima."""
    tam = [t * fator for t in o["tamanho"]]
    if o.get("tipo") != "recipiente":
        horiz = min(tam[:2]) if o.get("tipo") == "caixa" else tam[0]
        if horiz > GARRA_MAX:
            tam = [t * GARRA_MAX / horiz for t in tam]
    o["tamanho"] = tam


def variar(cena: dict, rng: np.random.Generator, forca: float = 1.0, tamanho: float = 0.0,
           pior_caso: bool = False) -> dict:
    """tamanho: erro de medida da visão (0,15 = 15%). O recipiente sai de 0 a 15% menor e mais raso,
    os objetos ±7,5%. pior_caso: recipiente 15% menor e objetos 7,5% maiores, sempre."""
    c = copy.deepcopy(cena)
    for o in c["objetos"]:
        if tamanho > 0:
            rec = o.get("tipo") == "recipiente"
            if pior_caso:
                fator = 1 - tamanho if rec else 1 + tamanho / 2
            else:
                fator = rng.uniform(1 - tamanho, 1) if rec else rng.uniform(1 - tamanho / 2, 1 + tamanho / 2)
            variar_tamanho(o, fator)
        if o.get("tipo") == "recipiente":
            o["pos"] = [o["pos"][0] + rng.uniform(-0.02, 0.02) * forca, o["pos"][1] + rng.uniform(-0.02, 0.02) * forca]
            continue
        o["pos"] = [o["pos"][0] + rng.uniform(-0.04, 0.04) * forca, o["pos"][1] + rng.uniform(-0.04, 0.04) * forca]
        o["yaw"] = float(o.get("yaw", 0)) + rng.uniform(-0.6, 0.6) * forca
        o["massa"] = float(o.get("massa", 0.1)) * rng.uniform(0.7, 1.3)
    validar_cena(c)
    return c


def rodar_episodio(cena: dict, saida: Path, idx: int, rng: np.random.Generator,
                   imagens: bool = False, forca: float = 1.0) -> dict:
    c = variar(cena, rng, forca) if forca > 0 else copy.deepcopy(cena)
    m, _ = compilar(c)
    d = mujoco.MjData(m)
    ir_para_casa(m, d)
    for _ in range(250):
        mujoco.mj_step(m, d)
    t0 = d.time
    tarefa = c["tarefa"]
    g = Gerador(m, d, tarefa["pegar"], tarefa["destino"], rng)

    serie = {k: [] for k in ("t", "qpos", "ctrl", "tcp", "obj", "fase")}
    fotos = {"cima": [], "pulso": []}
    rend = mujoco.Renderer(m, 128, 128) if imagens else None
    passo = [0]

    def gravar(fase):
        serie["t"].append(d.time - t0)
        serie["qpos"].append(d.qpos[g.qadr].copy())
        serie["ctrl"].append(d.ctrl[:8].copy())
        serie["tcp"].append(d.site_xpos[g.tcp].copy())
        serie["obj"].append(g.pos_objeto())
        serie["fase"].append(FASES.index(fase.nome) if fase.nome in FASES else -1)
        if rend is not None and passo[0] % 5 == 0:
            for cam in fotos:
                rend.update_scene(d, cam)
                fotos[cam].append(rend.render().copy())
        passo[0] += 1

    res = g.executar(gravar)
    if rend is not None:
        rend.close()

    nome = f"ep_{idx:04d}"
    arrays = {k: np.asarray(v, dtype=np.float32 if k != "fase" else np.int8) for k, v in serie.items()}
    if imagens:
        arrays.update({f"img_{k}": np.asarray(v, dtype=np.uint8) for k, v in fotos.items()})
    np.savez_compressed(saida / f"{nome}.npz", **arrays)

    anot = anotar(c, res, t0)
    (saida / f"{nome}.json").write_text(json.dumps(anot, ensure_ascii=False, indent=1), encoding="utf-8")
    return anot


def anotar(cena: dict, res, t0: float) -> dict:
    """Anotação 'em retrospecto': como o motor sabe o que fez, rotula cada trecho do episódio."""
    subtarefas = []
    for f in res.fases:
        if f.fim <= 0:
            continue
        prim = {"primitiva": f.rotulo, "fase": f.nome,
                "inicio": round(f.inicio - t0, 3), "fim": round(f.fim - t0, 3)}
        if subtarefas and subtarefas[-1]["subtarefa"] == f.subtarefa:
            subtarefas[-1]["primitivas"].append(prim)
            subtarefas[-1]["fim"] = prim["fim"]
        else:
            subtarefas.append({"subtarefa": f.subtarefa, "inicio": prim["inicio"], "fim": prim["fim"],
                               "primitivas": [prim]})
    tarefa = cena["tarefa"]
    return {
        "nivel_1_objetivo": tarefa.get("descricao") or f"pôr {tarefa['pegar']} em {tarefa['destino']}",
        "nivel_2_subtarefas": subtarefas,
        "nivel_4_eventos": [{**e, "t": round(e["t"] - t0, 3)} for e in res.eventos],
        "qualidade": {"sucesso": res.sucesso, "motivo": res.motivo,
                      "peso_no_treino": 1.0 if res.sucesso else 0.0},
        "duracao_s": round(res.duracao - t0, 3),
        "variacao": {o["nome"]: {"pos": [round(p, 4) for p in o["pos"]], "yaw": round(o.get("yaw", 0), 3),
                                 "massa": round(o.get("massa", 0.1), 4)}
                     for o in cena["objetos"]},
    }


def gerar(cena: dict, saida: str | Path, n: int, semente: int = 0, imagens: bool = False,
          forca: float = 1.0, log=print) -> dict:
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(semente)
    ok, motivos, t_ini = 0, {}, time.time()
    for i in range(n):
        a = rodar_episodio(cena, saida, i, rng, imagens, forca)
        q = a["qualidade"]
        ok += q["sucesso"]
        if not q["sucesso"]:
            motivos[q["motivo"]] = motivos.get(q["motivo"], 0) + 1
        log(f"  ep {i:04d}: {'ok   ' if q['sucesso'] else 'falha'} {a['duracao_s']:5.2f} s  {'' if q['sucesso'] else q['motivo']}")
    resumo = {"episodios": n, "sucessos": ok, "taxa_sucesso": round(ok / max(n, 1), 3),
              "falhas_por_motivo": motivos, "semente": semente, "imagens": imagens,
              "tempo_real_s": round(time.time() - t_ini, 1), "cpu": os.cpu_count()}
    (saida / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
    return resumo
