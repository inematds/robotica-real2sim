"""Renderiza um episódio em MP4 (30 fps) com a fase atual escrita na tela."""
from __future__ import annotations

import copy
from pathlib import Path

import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .cena2mjcf import compilar
from .episodios import variar
from .gerador import Gerador, ir_para_casa

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _fonte(tam):
    try:
        return ImageFont.truetype(FONTE, tam)
    except OSError:
        return ImageFont.load_default()


def filmar(cena: dict, arquivo: str | Path, cameras=("geral",), largura=1280, altura=720,
           semente: int | None = None, legenda: bool = True, fps: int = 30,
           passos: list[dict] | None = None, titulo: str = "") -> dict:
    c = variar(cena, np.random.default_rng(semente)) if semente is not None else copy.deepcopy(cena)
    m, _ = compilar(c)
    d = mujoco.MjData(m)
    ir_para_casa(m, d)
    for _ in range(250):
        mujoco.mj_step(m, d)
    passos = passos or [{"pegar": c["tarefa"]["pegar"], "destino": c["tarefa"]["destino"]}]

    cams = list(cameras)
    # 1 câmera: quadro inteiro; 2-3: a primeira grande e as outras empilhadas à direita
    if len(cams) == 1:
        tamanhos = [(largura, altura)]
    else:
        lw = int(largura * 0.68)
        tamanhos = [(lw, altura)] + [(largura - lw, altura // (len(cams) - 1))] * (len(cams) - 1)
    rends = [mujoco.Renderer(m, h, w) for (w, h) in tamanhos]
    f_grande, f_peq = _fonte(int(altura * 0.042)), _fonte(int(altura * 0.026))
    escritor = imageio.get_writer(str(arquivo), fps=fps, codec="libx264", quality=8,
                                  macro_block_size=8, ffmpeg_params=["-pix_fmt", "yuv420p"])
    estado = {"prox": 0.0, "fase": "", "n": 0}

    def quadro(fase):
        if d.time < estado["prox"]:
            return
        estado["prox"] += 1.0 / fps
        tela = Image.new("RGB", (largura, altura))
        x = 0
        for i, (cam, r, (w, h)) in enumerate(zip(cams, rends, tamanhos)):
            r.update_scene(d, cam)
            img = Image.fromarray(r.render())
            if i == 0:
                tela.paste(img, (0, 0)); x = w
            else:
                tela.paste(img, (x, (i - 1) * h))
                ImageDraw.Draw(tela).text((x + 12, (i - 1) * h + 8), cam, font=f_peq, fill=(250, 204, 21))
        if legenda:
            dr = ImageDraw.Draw(tela)
            txt = f"{fase.subtarefa.upper()} · {fase.rotulo}"
            dr.rounded_rectangle((20, altura - int(altura * 0.1), 30 + dr.textlength(txt, font=f_grande) + 20,
                                  altura - 20), radius=10, fill=(12, 12, 16))
            dr.text((40, altura - int(altura * 0.09)), txt, font=f_grande, fill=(250, 204, 21))
            dr.text((24, 18), f"t = {d.time:5.2f} s  (simulação MuJoCo)", font=f_peq, fill=(235, 235, 235))
            if titulo:
                dr.text((24, 18 + int(altura * 0.04)), titulo, font=f_peq, fill=(250, 204, 21))
        escritor.append_data(np.asarray(tela))
        estado["n"] += 1

    resultados = []
    for p in passos:
        g = Gerador(m, d, p["pegar"], p["destino"], vaga=tuple(p.get("vaga", (0.0, 0.0))),
                    deitar=bool(p.get("deitar")))
        res = g.executar(quadro)
        resultados.append(res)
        if not res.sucesso:
            break
    for _ in range(int(fps * 0.8)):  # segura o último quadro
        escritor.append_data(np.asarray(tela_final(rends, cams, tamanhos, d, largura, altura)))
    escritor.close()
    for r in rends:
        r.close()
    ok = len(resultados) == len(passos) and all(r.sucesso for r in resultados)
    return {"sucesso": ok, "motivo": "; ".join(r.motivo for r in resultados), "quadros": estado["n"],
            "arquivo": str(arquivo)}


def tela_final(rends, cams, tamanhos, d, largura, altura):
    tela = Image.new("RGB", (largura, altura))
    x = 0
    for i, (cam, r, (w, h)) in enumerate(zip(cams, rends, tamanhos)):
        r.update_scene(d, cam)
        img = Image.fromarray(r.render())
        if i == 0:
            tela.paste(img, (0, 0)); x = w
        else:
            tela.paste(img, (x, (i - 1) * h))
    return tela


def foto_da_cena(cena: dict, arquivo: str | Path, camera="cima", largura=1280, altura=720) -> None:
    m, _ = compilar(cena)
    d = mujoco.MjData(m)
    ir_para_casa(m, d)
    for _ in range(250):
        mujoco.mj_step(m, d)
    r = mujoco.Renderer(m, altura, largura)
    r.update_scene(d, camera)
    Image.fromarray(r.render()).save(arquivo)
    r.close()
