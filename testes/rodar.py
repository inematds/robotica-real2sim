#!/usr/bin/env python3
"""Testes do robotica-real2sim (sem rede, sem Codex): `python3 testes/rodar.py` (~1 min)."""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402

from real2sim.cena2mjcf import carregar_cena, compilar, validar_cena  # noqa: E402
from real2sim.episodios import gerar  # noqa: E402
from real2sim.foto2cena import extrair_json, para_referencial_do_robo  # noqa: E402
from real2sim.provar import distribuir_vagas, provar  # noqa: E402

FOTO = carregar_cena(RAIZ / "exemplos/mesa-foto/cena.json")
TESTE = carregar_cena(RAIZ / "exemplos/mesa-teste/cena.json")
falhas = []


def caso(nome):
    def deco(f):
        try:
            f()
            print(f"ok    {nome}")
        except Exception as e:  # noqa: BLE001
            falhas.append(nome)
            print(f"FALHA {nome}: {e}")
        return f
    return deco


@caso("cena fora do alcance é recusada")
def _():
    c = json.loads(json.dumps(TESTE))
    c["objetos"][0]["pos"] = [1.2, 0.0]
    try:
        validar_cena(c)
    except ValueError:
        return
    raise AssertionError("aceitou objeto a 1,2 m")


@caso("tarefa com objeto inexistente é recusada")
def _():
    c = json.loads(json.dumps(TESTE))
    c["tarefa"]["pegar"] = "unicornio"
    try:
        validar_cena(c)
    except ValueError:
        return
    raise AssertionError("aceitou objeto inexistente")


@caso("as duas cenas compilam com o Panda (7 juntas + garra)")
def _():
    for c in (FOTO, TESTE):
        m, xml = compilar(c)
        assert m.nu == 8, m.nu
        assert "tcp" in xml


@caso("resposta do modelo de visão -> referencial do robô (cm -> m, dentro do alcance)")
def _():
    bruta = extrair_json('lixo antes {"mesa":{"largura_cm":120,"profundidade_cm":80,"cor":"bege"},'
                         '"objetos":[{"nome":"cubo","tipo":"caixa","tamanho":[5,5,5],"pos_cm":[10,0],'
                         '"cor":"vermelho","massa_g":80},{"nome":"bandeja","tipo":"recipiente",'
                         '"tamanho":[20,16,5],"pos_cm":[40,-30],"cor":"cinza"}],'
                         '"tarefa":{"pegar":"cubo","destino":"bandeja"}} lixo depois')
    cena, avisos = para_referencial_do_robo(bruta)
    validar_cena(cena)
    assert cena["objetos"][0]["tamanho"] == [0.05, 0.05, 0.05]
    assert cena["objetos"][0]["pos"][0] >= 0.3, "não empurrou o objeto da borda para o alcance"
    assert any("empurrada" in a for a in avisos)


@caso("cada objeto das duas cenas vai para o recipiente (5 variações cada)")
def _():
    for c in (FOTO, TESTE):
        dest = [o["nome"] for o in c["objetos"] if o["tipo"] == "recipiente"][0]
        for o in c["objetos"]:
            if o["tipo"] == "recipiente":
                continue
            r = provar(c, [{"pegar": o["nome"], "destino": dest}], n=5, log=lambda *a: None)
            assert r["planos_completos"] >= 4, f"{o['nome']}: {r['planos_completos']}/5"


@caso("episódios gravam série temporal e anotação em 4 níveis")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        r = gerar(TESTE, tmp, 3, semente=1, imagens=True, log=lambda *a: None)
        assert r["episodios"] == 3
        z = np.load(Path(tmp) / "ep_0000.npz")
        assert z["qpos"].shape[1] == 7 and len(z["t"]) > 100
        assert z["img_pulso"].shape[1:] == (128, 128, 3)
        a = json.loads((Path(tmp) / "ep_0000.json").read_text())
        assert a["nivel_1_objetivo"]
        assert [s["subtarefa"] for s in a["nivel_2_subtarefas"]][:3] == ["pegar", "levar", "soltar"]
        assert len(a["nivel_2_subtarefas"][0]["primitivas"]) == 3
        assert a["qualidade"]["peso_no_treino"] in (0.0, 1.0)


@caso("vagas: dois objetos no mesmo recipiente ganham lugares diferentes")
def _():
    passos = distribuir_vagas(FOTO, [{"pegar": "lata_azul", "destino": "bandeja_cinza"},
                                     {"pegar": "bola_tenis", "destino": "bandeja_cinza"}])
    assert passos[0]["vaga"] != passos[1]["vaga"]


@caso("a prova na simulação separa o plano ruim do bom (sem vagas < com vagas)")
def _():
    passos = [{"pegar": "lata_azul", "destino": "bandeja_cinza"},
              {"pegar": "bola_tenis", "destino": "bandeja_cinza"}]
    ruim = provar(FOTO, passos, n=6, log=lambda *a: None)
    bom = provar(FOTO, distribuir_vagas(FOTO, passos), n=6, log=lambda *a: None)
    assert bom["planos_completos"] > ruim["planos_completos"], (ruim["planos_completos"], bom["planos_completos"])
    assert bom["planos_completos"] >= 5


@caso("erro de medida: pior caso encolhe o recipiente 15% e não passa da garra")
def _():
    from real2sim.episodios import variar
    c = variar(FOTO, np.random.default_rng(0), tamanho=0.15, pior_caso=True)
    t = {o["nome"]: o["tamanho"] for o in c["objetos"]}
    t0 = {o["nome"]: o["tamanho"] for o in FOTO["objetos"]}
    assert abs(t["bandeja_cinza"][0] - 0.85 * t0["bandeja_cinza"][0]) < 1e-9
    assert t["lata_azul"][0] > t0["lata_azul"][0] and max(t["cubo_vermelho"][:2]) <= 0.078 + 1e-9


print()
LEROBOT = RAIZ / ".venv-lerobot/bin/python"
if not LEROBOT.exists():
    print("pulado exportar para o LeRobot (sem .venv-lerobot; ./instalar.sh --lerobot)")
else:
    @caso("episódios com câmeras -> dataset LeRobot que abre de volta")
    def _():
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            gerar(FOTO, Path(tmp) / "eps", 2, imagens=True, log=lambda *_: None)
            r = subprocess.run([str(LEROBOT), "-m", "real2sim.exportar", f"{tmp}/eps", f"{tmp}/ds"],
                               cwd=RAIZ, capture_output=True, text=True, timeout=300)
            assert r.returncode == 0, r.stderr[-500:]
            linha = [x for x in r.stdout.splitlines() if x.startswith("conferido:")]
            assert linha and "'episodios': 2" in linha[0] and "'fps': 10" in linha[0], r.stdout[-500:]
            assert "observation.images.cima" in linha[0] and "(7,)" in linha[0] and "(8,)" in linha[0]

print("TUDO OK" if not falhas else f"{len(falhas)} FALHA(S): {falhas}")
sys.exit(1 if falhas else 0)
