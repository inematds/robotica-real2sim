"""Provar uma ação na simulação antes de mandar para o robô real.

1. planejar(): um modelo de linguagem (Codex pela assinatura) lê a cena e um pedido em português
   ("arrume a mesa: tudo que rola vai para a bandeja") e devolve um plano em passos pegar->destino.
2. provar(): o plano roda N vezes no gêmeo de simulação, cada vez com pequenas variações; só passa
   se a taxa de sucesso ficar acima do mínimo. O relatório diz qual passo falha e por quê.
"""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path

import mujoco
import numpy as np

from .cena2mjcf import compilar
from .episodios import variar
from .foto2cena import extrair_json
from .gerador import Gerador, ir_para_casa

PROMPT_PLANO = """Você controla um braço robótico com garra (abertura máxima 8 cm) diante desta mesa:
{cena}

Pedido do usuário: "{pedido}"

Monte um plano de passos pegar->destino usando SOMENTE os nomes de objetos acima. O destino de
cada passo precisa ser um objeto do tipo "recipiente". Não invente objetos; se o pedido for
impossível, devolva passos vazios e explique em "obs".
Responda SOMENTE com JSON: {{"passos": [{{"pegar": "", "destino": ""}}], "obs": ""}}"""


def planejar(cena: dict, pedido: str, modelo: str | None = None, timeout: int = 600, motor: str = "codex") -> dict:
    resumo = [{k: o[k] for k in ("nome", "tipo", "tamanho", "pos", "cor")} for o in cena["objetos"]]
    prompt = PROMPT_PLANO.format(cena=json.dumps(resumo, ensure_ascii=False), pedido=pedido)
    if motor in ("gemini", "openrouter"):
        from .foto2cena import perguntar
        plano = extrair_json(perguntar(motor, prompt, None, modelo))
        return _conferir_plano(cena, plano, pedido)
    if motor == "claude":
        from .foto2cena import perguntar_claude
        plano = extrair_json(perguntar_claude(prompt, None, modelo, timeout))
        return _conferir_plano(cena, plano, pedido)
    modelo = modelo or "gpt-6-luna"
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "plano.txt"
        subprocess.run(["codex", "exec", "-m", modelo, "-s", "read-only", "--skip-git-repo-check",
                        "-o", str(saida), "-"], input=prompt, text=True, capture_output=True,
                       timeout=timeout, cwd=tmp)
        if not saida.exists():
            raise RuntimeError("o Codex não devolveu o plano (confira `codex login`)")
        plano = extrair_json(saida.read_text(encoding="utf-8"))
    return _conferir_plano(cena, plano, pedido)


def _conferir_plano(cena: dict, plano: dict, pedido: str) -> dict:
    nomes = {o["nome"]: o for o in cena["objetos"]}
    for p in plano.get("passos", []):
        if p["pegar"] not in nomes or p["destino"] not in nomes:
            raise ValueError(f"plano cita objeto que não existe: {p}")
        if nomes[p["destino"]]["tipo"] != "recipiente":
            raise ValueError(f"destino não é recipiente: {p['destino']}")
    plano["pedido"] = pedido
    return plano


def distribuir_vagas(cena: dict, passos: list[dict]) -> list[dict]:
    """Objetos que vão para o mesmo recipiente ganham lugares diferentes ao longo do lado maior."""
    tam = {o["nome"]: o["tamanho"] for o in cena["objetos"]}
    por_destino: dict[str, list[dict]] = {}
    novos = [dict(p) for p in passos]
    for p in novos:
        por_destino.setdefault(p["destino"], []).append(p)
    for destino, lista in por_destino.items():
        n = len(lista)
        if n == 1:
            continue
        lx, ly = tam[destino][0], tam[destino][1]
        eixo = 0 if lx >= ly else 1
        util = (lx if eixo == 0 else ly) - 0.07  # sobra das paredes e da garra
        for k, p in enumerate(lista):
            off = -util / 2 + util * k / (n - 1)
            p.setdefault("vaga", [off, 0.0] if eixo == 0 else [0.0, off])
    return novos


def rodar_plano(cena: dict, passos: list[dict], rng: np.random.Generator | None, forca: float = 1.0,
                tamanho: float = 0.0, pior_caso: bool = False) -> list:
    c = variar(cena, rng, forca, tamanho, pior_caso) if rng is not None else copy.deepcopy(cena)
    m, _ = compilar(c)
    d = mujoco.MjData(m)
    ir_para_casa(m, d)
    for _ in range(250):
        mujoco.mj_step(m, d)
    resultados = []
    for p in passos:
        g = Gerador(m, d, p["pegar"], p["destino"], vaga=tuple(p.get("vaga", (0.0, 0.0))))
        r = g.executar()
        resultados.append({"passo": p, "sucesso": r.sucesso, "motivo": r.motivo})
        if not r.sucesso:
            break
    # um passo posterior pode derrubar o que já estava no lugar: confere tudo no fim
    for res in resultados:
        if res["sucesso"]:
            g = Gerador(m, d, res["passo"]["pegar"], res["passo"]["destino"])
            if not g.dentro_do_destino():
                res["sucesso"], res["motivo"] = False, "saiu do destino num passo seguinte"
    return resultados


def provar(cena: dict, passos: list[dict], n: int = 20, minimo: float = 0.9, semente: int = 0,
           log=print, tamanho: float = 0.0, pior_caso: bool = False) -> dict:
    """tamanho > 0: a física roda com objetos de tamanho diferente do medido (as vagas continuam
    calculadas sobre a medida), como acontece quando a visão erra a escala."""
    rng = np.random.default_rng(semente)
    por_passo = [{"passo": p, "ok": 0, "falhas": {}} for p in passos]
    completos = 0
    for i in range(n):
        res = rodar_plano(cena, passos, rng, tamanho=tamanho, pior_caso=pior_caso)
        tudo = len(res) == len(passos) and all(r["sucesso"] for r in res)
        completos += tudo
        for j, r in enumerate(res):
            if r["sucesso"]:
                por_passo[j]["ok"] += 1
            else:
                f = por_passo[j]["falhas"]
                f[r["motivo"]] = f.get(r["motivo"], 0) + 1
        log(f"  tentativa {i + 1:3d}/{n}: {'plano completo' if tudo else 'falhou no passo ' + str(len(res))}")
    taxa = completos / max(n, 1)
    return {"tentativas": n, "planos_completos": completos, "taxa": round(taxa, 3), "minimo": minimo,
            "aprovado": taxa >= minimo, "var_tamanho": tamanho, "pior_caso": pior_caso, "por_passo": por_passo}
