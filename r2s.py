#!/usr/bin/env python3
"""r2s — da foto da mesa ao gêmeo de simulação, aos dados de treino e à prova do plano.

  r2s.py foto      <foto.jpg> <cena.json> [--pedido "..."] [--motor codex|claude|gemini|openrouter] [--esforco high]
  r2s.py ver       <cena.json> <saida.png> [--camera cima|geral|frente]
  r2s.py xml       <cena.json> <saida.xml>
  r2s.py filmar    <cena.json> <saida.mp4> [--cameras geral,cima,pulso] [--plano p.json] [--sem-vagas]
  r2s.py episodios <cena.json> <pasta> [-n 50] [--imagens] [--semente 0]
  r2s.py planejar  <cena.json> "<pedido em português>" <plano.json> [--motor codex|claude|gemini|openrouter] [--esforco high]
  r2s.py provar    <cena.json> <plano.json> [-n 20] [--minimo 0.9] [--sem-vagas] [--var-tamanho 0.15] [--pior-caso] [--deitar]
  r2s.py tudo      <foto.jpg> <pasta> [--pedido "..."] [-n 50]
  r2s.py exportar  <pasta-episodios> <saida> [--com-falhas] [--sobrescrever]   (dataset LeRobot)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
_RAIZ = Path(__file__).resolve().parent
_VENV = _RAIZ / ".venv/bin/python"
if _VENV.exists() and Path(sys.prefix).resolve() != (_RAIZ / ".venv").resolve():
    os.execv(str(_VENV), [str(_VENV), *sys.argv])  # roda no venv criado pelo instalar.sh
sys.path.insert(0, str(_RAIZ))

from real2sim.cena2mjcf import carregar_cena, compilar  # noqa: E402


def salvar(obj, caminho):
    Path(caminho).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def _uso(a, destino):
    """No motor gemini, grava os tokens da chamada ao lado do arquivo (<arquivo>.uso.json)."""
    if a.motor not in ("gemini", "openrouter"):
        return
    from real2sim.foto2cena import ULTIMO_USO
    salvar(dict(ULTIMO_USO), Path(destino).with_suffix(".uso.json"))
    print("uso:", {k: v for k, v in ULTIMO_USO.items() if "oken" in k or k == "cost"})


def cmd_foto(a):
    from real2sim.foto2cena import foto_para_cena
    cena, avisos, _ = foto_para_cena(a.foto, a.referencia, a.pedido, a.modelo, a.motor)
    salvar(cena, a.cena)
    for av in avisos:
        print("aviso:", av)
    _uso(a, a.cena)
    print(f"cena: {len(cena['objetos'])} objetos -> {a.cena}")
    print("tarefa:", cena.get("tarefa", {}).get("descricao", "-"))
    if cena.get("confianca"):
        print("incerteza declarada pelo modelo:", cena["confianca"])


def cmd_ver(a):
    from real2sim.filmar import foto_da_cena
    foto_da_cena(carregar_cena(a.cena), a.saida, a.camera)
    print("imagem:", a.saida)


def cmd_xml(a):
    m, xml = compilar(carregar_cena(a.cena))
    Path(a.saida).write_text(xml, encoding="utf-8")
    print(f"MJCF: {m.nbody} corpos, {m.ngeom} geoms -> {a.saida}")


def cmd_filmar(a):
    from real2sim.filmar import filmar
    from real2sim.provar import distribuir_vagas, marcar_deitar
    cena, passos = carregar_cena(a.cena), None
    if getattr(a, "plano", None):
        passos = json.loads(Path(a.plano).read_text(encoding="utf-8"))["passos"]
        passos = marcar_deitar(cena, passos) if a.deitar else passos
        passos = passos if a.sem_vagas else distribuir_vagas(cena, passos)
    r = filmar(cena, a.saida, tuple(a.cameras.split(",")), a.largura, a.altura, a.semente,
               passos=passos, titulo=getattr(a, "titulo", "") or "")
    print(("sucesso: " if r["sucesso"] else "falha: ") + r["motivo"], f"({r['quadros']} quadros) -> {a.saida}")


def cmd_episodios(a):
    from real2sim.episodios import gerar
    r = gerar(carregar_cena(a.cena), a.pasta, a.n, a.semente, a.imagens)
    print(f"{r['sucessos']}/{r['episodios']} episódios com sucesso ({r['taxa_sucesso']:.0%}) "
          f"em {r['tempo_real_s']} s -> {a.pasta}")


def cmd_exportar(a):
    """Dataset LeRobot. Roda na venv .venv-lerobot (instalar.sh --lerobot); esta venv só tem MuJoCo."""
    import subprocess
    py = Path(__file__).resolve().parent / ".venv-lerobot" / "bin" / "python"
    if not py.exists():
        sys.exit("falta a venv do LeRobot: ./instalar.sh --lerobot")
    args = [str(py), "-m", "real2sim.exportar", str(Path(a.episodios).resolve()), str(Path(a.saida).resolve()), "--repo-id", a.repo_id]
    args += ["--com-falhas"] * a.com_falhas + ["--sobrescrever"] * a.sobrescrever
    sys.exit(subprocess.call(args, cwd=Path(__file__).resolve().parent))


def cmd_planejar(a):
    from real2sim.provar import planejar
    plano = planejar(carregar_cena(a.cena), a.pedido, a.modelo, motor=a.motor)
    plano["motor"] = a.motor
    _uso(a, a.plano)
    salvar(plano, a.plano)
    for p in plano["passos"]:
        print(f"  pegar {p['pegar']} -> {p['destino']}")
    if plano.get("obs"):
        print("obs:", plano["obs"])


def cmd_provar(a):
    from real2sim.provar import distribuir_vagas, marcar_deitar, provar
    plano = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    cena = carregar_cena(a.cena)
    passos = marcar_deitar(cena, plano["passos"]) if a.deitar else plano["passos"]
    passos = passos if a.sem_vagas else distribuir_vagas(cena, passos)
    tam = a.var_tamanho if a.var_tamanho is not None else (0.15 if a.pior_caso else 0.0)
    r = provar(cena, passos, a.n, a.minimo, a.semente, tamanho=tam, pior_caso=a.pior_caso)
    r["vagas"] = not a.sem_vagas
    sufixo = ".prova" + "-sem-vagas" * a.sem_vagas + "-deitar" * a.deitar + "-pior" * a.pior_caso + "-tamanho" * (tam > 0 and not a.pior_caso) + ".json"
    salvar(r, Path(a.plano).with_suffix(sufixo))
    print(f"plano completo em {r['planos_completos']}/{r['tentativas']} ({r['taxa']:.0%}); "
          f"mínimo {a.minimo:.0%} -> {'APROVADO para o robô real' if r['aprovado'] else 'REPROVADO: não mande ao robô'}")
    for p in r["por_passo"]:
        print(f"  {p['passo']['pegar']} -> {p['passo']['destino']}: {p['ok']} ok", p["falhas"] or "")
    sys.exit(0 if r["aprovado"] else 2)


def cmd_tudo(a):
    pasta = Path(a.pasta); pasta.mkdir(parents=True, exist_ok=True)
    a.cena = str(pasta / "cena.json")
    cmd_foto(a)
    a.saida, a.camera = str(pasta / "gemeo-cima.png"), "cima"; cmd_ver(a)
    a.saida, a.cameras, a.semente = str(pasta / "episodio.mp4"), "geral,cima,pulso", None; cmd_filmar(a)
    a.pasta, a.semente, a.imagens = str(pasta / "episodios"), 0, False; cmd_episodios(a)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    m = None  # padrão do motor: gpt-6-luna (codex) ou INEMA_CLAUDE_TOPO (claude)

    x = s.add_parser("foto"); x.add_argument("foto"); x.add_argument("cena")
    x.add_argument("--pedido", default=""); x.add_argument("--referencia", default="uma folha A4 (21 x 29,7 cm)")
    x.add_argument("--modelo", default=m); x.add_argument("--motor", choices=["codex", "claude", "gemini", "openrouter"], default="codex"); x.add_argument("--esforco", choices=["low", "medium", "high", "xhigh", "max"], help="esforço de raciocínio (codex/claude; padrão do CLI)"); x.set_defaults(f=cmd_foto)

    x = s.add_parser("ver"); x.add_argument("cena"); x.add_argument("saida")
    x.add_argument("--camera", default="cima"); x.set_defaults(f=cmd_ver)

    x = s.add_parser("xml"); x.add_argument("cena"); x.add_argument("saida"); x.set_defaults(f=cmd_xml)

    x = s.add_parser("filmar"); x.add_argument("cena"); x.add_argument("saida")
    x.add_argument("--cameras", default="geral"); x.add_argument("--semente", type=int, default=None)
    x.add_argument("--largura", type=int, default=1280); x.add_argument("--altura", type=int, default=720)
    x.add_argument("--plano", help="plano.json com vários passos"); x.add_argument("--sem-vagas", action="store_true")
    x.add_argument("--deitar", action="store_true")
    x.add_argument("--titulo", default=""); x.set_defaults(f=cmd_filmar)

    x = s.add_parser("episodios"); x.add_argument("cena"); x.add_argument("pasta")
    x.add_argument("-n", type=int, default=50); x.add_argument("--semente", type=int, default=0)
    x.add_argument("--imagens", action="store_true"); x.set_defaults(f=cmd_episodios)

    x = s.add_parser("exportar"); x.add_argument("episodios"); x.add_argument("saida")
    x.add_argument("--repo-id", default="local/real2sim"); x.add_argument("--com-falhas", action="store_true")
    x.add_argument("--sobrescrever", action="store_true"); x.set_defaults(f=cmd_exportar)

    x = s.add_parser("planejar"); x.add_argument("cena"); x.add_argument("pedido"); x.add_argument("plano")
    x.add_argument("--modelo", default=m); x.add_argument("--motor", choices=["codex", "claude", "gemini", "openrouter"], default="codex"); x.add_argument("--esforco", choices=["low", "medium", "high", "xhigh", "max"], help="esforço de raciocínio (codex/claude; padrão do CLI)"); x.set_defaults(f=cmd_planejar)

    x = s.add_parser("provar"); x.add_argument("cena"); x.add_argument("plano")
    x.add_argument("-n", type=int, default=20); x.add_argument("--minimo", type=float, default=0.9)
    x.add_argument("--semente", type=int, default=0)
    x.add_argument("--sem-vagas", action="store_true", help="todos no centro do recipiente (mostra o erro)")
    x.add_argument("--var-tamanho", type=float, default=None,
                   help="erro de medida da visão, ex.: 0.15 (recipiente até 15%% menor, objetos ±7,5%%)")
    x.add_argument("--pior-caso", action="store_true", help="recipiente 15%% menor e objetos 7,5%% maiores")
    x.add_argument("--deitar", action="store_true", help="lata mais alta que 2x a borda vai deitada (60 graus)")
    x.set_defaults(f=cmd_provar)

    x = s.add_parser("tudo"); x.add_argument("foto"); x.add_argument("pasta")
    x.add_argument("--pedido", default=""); x.add_argument("--referencia", default="uma folha A4 (21 x 29,7 cm)")
    x.add_argument("--modelo", default=m); x.add_argument("--motor", choices=["codex", "claude", "gemini", "openrouter"], default="codex"); x.add_argument("--esforco", choices=["low", "medium", "high", "xhigh", "max"], help="esforço de raciocínio (codex/claude; padrão do CLI)"); x.add_argument("-n", type=int, default=50)
    x.add_argument("--largura", type=int, default=1280); x.add_argument("--altura", type=int, default=720)
    x.set_defaults(f=cmd_tudo)

    a = p.parse_args()
    if getattr(a, "esforco", None):
        import real2sim.foto2cena as f2c
        f2c.ESFORCO = a.esforco
    a.f(a)


if __name__ == "__main__":
    main()
