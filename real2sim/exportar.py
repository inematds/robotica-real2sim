"""Exporta os episódios do gerador (ep_NNNN.npz + .json) para um dataset LeRobot (API oficial).

Roda na venv do LeRobot (`.venv-lerobot`, ver requirements-lerobot.txt): só precisa de numpy e lerobot,
não de MuJoCo. Uso direto: `.venv-lerobot/bin/python -m real2sim.exportar <episodios> <saida>`;
o `r2s.py exportar` chama isto sozinho.

Alinhamento: o gerador grava o estado a 50 Hz e as câmeras a cada 5 passos (10 Hz). O LeRobot exige
todas as colunas no mesmo quadro, então com imagens o dataset sai a 10 Hz (estado e ação amostrados nos
mesmos passos das fotos); sem imagens, a 50 Hz. O timestamp de cada quadro é índice / fps.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

PASSO_FOTO = 5          # episodios.py grava uma foto a cada 5 passos de controle
FPS_ESTADO = 50
JUNTAS = [f"junta{i}" for i in range(1, 8)]
ACOES = JUNTAS + ["garra"]


def _episodios(pasta: Path) -> list[Path]:
    return sorted(pasta.glob("ep_*.npz"))


def exportar(pasta: str | Path, saida: str | Path, repo_id: str = "local/real2sim",
             com_falhas: bool = False, sobrescrever: bool = False, log=print) -> dict:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    pasta, saida = Path(pasta), Path(saida)
    eps = _episodios(pasta)
    if not eps:
        raise SystemExit(f"nenhum ep_*.npz em {pasta}")
    if saida.exists():
        if not sobrescrever:
            raise SystemExit(f"{saida} já existe (use --sobrescrever)")
        shutil.rmtree(saida)

    z0 = np.load(eps[0])
    cams = sorted(k[4:] for k in z0.files if k.startswith("img_"))
    fps = FPS_ESTADO // PASSO_FOTO if cams else FPS_ESTADO
    features = {
        "observation.state": {"dtype": "float32", "shape": (len(JUNTAS),), "names": JUNTAS},
        "action": {"dtype": "float32", "shape": (len(ACOES),), "names": ACOES},
    }
    for c in cams:
        h, w, ch = z0[f"img_{c}"].shape[1:]
        features[f"observation.images.{c}"] = {"dtype": "video", "shape": (h, w, ch),
                                               "names": ["height", "width", "channels"]}

    ds = LeRobotDataset.create(repo_id=repo_id, fps=fps, features=features, root=saida,
                               robot_type="franka_panda", use_videos=True)
    feitos, pulados, quadros = 0, 0, 0
    for npz in eps:
        anot = json.loads(npz.with_suffix(".json").read_text(encoding="utf-8"))
        if not com_falhas and not anot["qualidade"]["sucesso"]:
            pulados += 1
            continue
        z = np.load(npz)
        tarefa = anot["nivel_1_objetivo"]
        n = len(z[f"img_{cams[0]}"]) if cams else len(z["t"])
        idx = [min(k * PASSO_FOTO, len(z["t"]) - 1) for k in range(n)] if cams else list(range(n))
        for k, i in enumerate(idx):
            quadro = {"observation.state": z["qpos"][i].astype(np.float32),
                      "action": z["ctrl"][i].astype(np.float32), "task": tarefa}
            for c in cams:
                quadro[f"observation.images.{c}"] = z[f"img_{c}"][k]
            ds.add_frame(quadro)
        ds.save_episode()
        feitos += 1
        quadros += n
    ds.finalize()
    r = {"episodios": feitos, "pulados": pulados, "quadros": quadros, "fps": fps, "cameras": cams,
         "saida": str(saida), "repo_id": repo_id}
    log(f"{feitos} episódios, {quadros} quadros a {fps} Hz, câmeras {cams or 'nenhuma'} -> {saida}"
        + (f" ({pulados} falhas fora; use --com-falhas)" if pulados else ""))
    return r


def conferir(saida: str | Path, repo_id: str = "local/real2sim", log=print) -> dict:
    """Abre o dataset de volta pela API do LeRobot e lê um quadro (prova de que o formato vale)."""
    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    ds = LeRobotDataset(repo_id, root=saida)
    q = ds[len(ds) // 2]
    imgs = {k: tuple(v.shape) for k, v in q.items() if k.startswith("observation.images.")}
    r = {"episodios": ds.num_episodes, "quadros": ds.num_frames, "fps": ds.fps,
         "estado": tuple(q["observation.state"].shape), "acao": tuple(q["action"].shape),
         "imagens": imgs, "tarefa": q.get("task")}
    log(f"conferido: {r}")
    return r


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("episodios"); p.add_argument("saida")
    p.add_argument("--repo-id", default="local/real2sim")
    p.add_argument("--com-falhas", action="store_true", help="inclui episódios que falharam")
    p.add_argument("--sobrescrever", action="store_true")
    a = p.parse_args(argv)
    exportar(a.episodios, a.saida, a.repo_id, a.com_falhas, a.sobrescrever)
    conferir(a.saida, a.repo_id)


if __name__ == "__main__":
    sys.exit(main())
