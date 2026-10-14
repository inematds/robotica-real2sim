"""cena.json -> modelo MuJoCo (gêmeo de simulação da mesa).

A cena descreve a mesa e os objetos em metros, no referencial do robô:
x para frente (longe da base), y para a esquerda, z para cima, origem na base do braço
sobre o tampo. O braço é o Franka Panda do MuJoCo Menagerie.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mujoco

RAIZ = Path(__file__).resolve().parent.parent
PANDA = RAIZ / "vendor/menagerie/franka_emika_panda/panda.xml"

CORES = {
    "vermelho": (0.85, 0.15, 0.12), "azul": (0.15, 0.35, 0.85), "verde": (0.2, 0.7, 0.25),
    "amarelo": (0.98, 0.8, 0.08), "laranja": (0.95, 0.5, 0.1), "branco": (0.92, 0.92, 0.9),
    "preto": (0.08, 0.08, 0.1), "marrom": (0.5, 0.33, 0.2), "roxo": (0.5, 0.25, 0.7),
    "cinza": (0.55, 0.55, 0.58), "rosa": (0.95, 0.5, 0.65), "bege": (0.85, 0.75, 0.6),
}


def cor_rgba(cor) -> list[float]:
    if isinstance(cor, (list, tuple)):
        v = [float(c) for c in cor][:3]
        if max(v) > 1:
            v = [c / 255 for c in v]
        return v + [1.0]
    return list(CORES.get(str(cor).lower(), (0.6, 0.6, 0.6))) + [1.0]


def carregar_cena(caminho: str | Path) -> dict:
    cena = json.loads(Path(caminho).read_text(encoding="utf-8"))
    validar_cena(cena)
    return cena


def validar_cena(cena: dict) -> None:
    """Recusa cena fisicamente impossível para o braço (fora do alcance, grande demais)."""
    nomes = set()
    for o in cena["objetos"]:
        n = o["nome"]
        if n in nomes:
            raise ValueError(f"objeto repetido: {n}")
        nomes.add(n)
        x, y = o["pos"][:2]
        r = (x * x + y * y) ** 0.5
        if not 0.25 <= r <= 0.8:
            raise ValueError(f"{n}: a {r:.2f} m da base, fora do alcance do Panda (0,25–0,80 m)")
        if o.get("tipo", "caixa") not in ("caixa", "cilindro", "esfera", "recipiente"):
            raise ValueError(f"{n}: tipo desconhecido {o.get('tipo')}")
    t = cena.get("tarefa", {})
    for chave in ("pegar", "destino"):
        if t.get(chave) and t[chave] not in nomes:
            raise ValueError(f"tarefa.{chave} = {t[chave]} não existe na cena")


def montar_spec(cena: dict) -> mujoco.MjSpec:
    spec = mujoco.MjSpec.from_file(str(PANDA))
    spec.option.timestep = 0.002
    spec.option.impratio = 10
    spec.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
    spec.visual.global_.offwidth = 1920
    spec.visual.global_.offheight = 1080
    spec.visual.headlight.ambient = [0.35, 0.35, 0.35]

    # garra: o modelo do Menagerie aperta ~3 N; a garra real do Panda faz 70 N contínuos.
    # Rigidez 10x (aperto ~30 N), mesma faixa de comando 0-255.
    garra = spec.actuator("actuator8")
    garra.gainprm[0] = 0.04 / 255 * 1000
    garra.biasprm[1] = -1000
    garra.biasprm[2] = -60

    mundo = spec.worldbody
    # ponto de trabalho (TCP) entre os dedos
    mao = spec.body("hand")
    mao.add_site(name="tcp", pos=[0, 0, 0.1034], size=[0.006] * 3, rgba=[1, 0.2, 0.2, 0.0])

    mesa = cena.get("mesa", {})
    larg, prof = mesa.get("largura", 1.2), mesa.get("profundidade", 0.8)
    cx = mesa.get("centro_x", 0.5)
    tampo = cor_rgba(mesa.get("cor", "bege"))
    mundo.add_geom(name="chao", type=mujoco.mjtGeom.mjGEOM_PLANE, size=[3, 3, 0.05],
                   pos=[0, 0, -0.75], rgba=[0.18, 0.18, 0.2, 1])
    mundo.add_geom(name="tampo", type=mujoco.mjtGeom.mjGEOM_BOX, size=[prof / 2 + 0.15, larg / 2, 0.02],
                   pos=[cx - 0.075, 0, -0.02], rgba=tampo, friction=[1.0, 0.01, 0.001])
    for sx in (-1, 1):
        for sy in (-1, 1):
            mundo.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.03, 0.03, 0.365],
                           pos=[cx - 0.075 + sx * (prof / 2 + 0.1), sy * (larg / 2 - 0.05), -0.405],
                           rgba=[0.3, 0.25, 0.2, 1], contype=0, conaffinity=0)
    mundo.add_light(pos=[0.5, -0.6, 1.8], dir=[0, 0.3, -1], diffuse=[0.75, 0.75, 0.75], castshadow=True)
    mundo.add_light(pos=[0.9, 0.8, 1.5], dir=[-0.3, -0.4, -1], diffuse=[0.35, 0.35, 0.35])

    # câmeras: vista geral, de cima (como a foto) e no pulso
    mundo.add_camera(name="geral", pos=[1.55, -0.95, 0.85], xyaxes=[0.53, 0.85, 0, -0.33, 0.21, 0.92])
    mundo.add_camera(name="cima", pos=[cx, 0, 1.35], xyaxes=[0, -1, 0, 1, 0, 0])
    mundo.add_camera(name="frente", pos=[1.6, 0, 0.55], xyaxes=[0, 1, 0, -0.3, 0, 0.95])
    mao.add_camera(name="pulso", pos=[0.07, 0, 0.03], xyaxes=[-0.82, 0, -0.57, 0, 1, 0], fovy=80)

    for o in cena["objetos"]:
        adicionar_objeto(spec, mundo, o)
    return spec


def adicionar_objeto(spec, mundo, o: dict) -> None:
    tipo = o.get("tipo", "caixa")
    rgba = cor_rgba(o.get("cor", "cinza"))
    x, y = o["pos"][:2]
    yaw = float(o.get("yaw", 0.0))
    massa = float(o.get("massa", 0.1))
    tam = o["tamanho"]  # caixa/recipiente: [x,y,z] total; cilindro: [diam, altura]; esfera: [diam]
    atrito = [1.5, 0.06, 0.002]
    if tipo == "recipiente":
        # recipiente fixo e aberto em cima (bandeja/caixa de destino)
        sx, sy, sz = (t / 2 for t in tam)
        b = mundo.add_body(name=o["nome"], pos=[x, y, 0], quat=quat_yaw(yaw))
        e = 0.006
        b.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[sx, sy, e], pos=[0, 0, e], rgba=rgba)
        for px, py, hx, hy in ((sx - e, 0, e, sy), (-sx + e, 0, e, sy), (0, sy - e, sx, e), (0, -sy + e, sx, e)):
            b.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[hx, hy, sz], pos=[px, py, sz], rgba=rgba)
        b.add_site(name=o["nome"] + "_alvo", pos=[0, 0, 2 * e], size=[0.01] * 3, rgba=[0, 0, 0, 0])
        return
    if tipo == "caixa":
        meia = [t / 2 for t in tam]
        z = meia[2]
        g = dict(type=mujoco.mjtGeom.mjGEOM_BOX, size=meia)
    elif tipo == "cilindro":
        z = tam[1] / 2
        g = dict(type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[tam[0] / 2, tam[1] / 2, 0])
    else:
        z = tam[0] / 2
        g = dict(type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[tam[0] / 2, 0, 0])
    b = mundo.add_body(name=o["nome"], pos=[x, y, z + 0.001], quat=quat_yaw(yaw))
    b.add_freejoint(name=o["nome"] + "_livre")
    if tipo == "cilindro":
        # colisão como prisma de 24 lados (malha convexa): o contato cilindro x caixa do MuJoCo
        # devolvia a normal na vertical e os dedos atravessavam a lata; o visual segue cilindro
        nome_malha = o["nome"] + "_prisma"
        spec.add_mesh(name=nome_malha, uservert=_prisma(tam[0] / 2, tam[1] / 2, 24))
        b.add_geom(name=o["nome"] + "_geom", type=mujoco.mjtGeom.mjGEOM_MESH, meshname=nome_malha,
                   rgba=[0, 0, 0, 0], mass=massa, friction=atrito, condim=4)
        b.add_geom(contype=0, conaffinity=0, mass=0, rgba=rgba, **g)
        return
    b.add_geom(name=o["nome"] + "_geom", rgba=rgba, mass=massa, friction=atrito,
               condim=4, **g)


def _prisma(r: float, h: float, lados: int) -> list[float]:
    import math
    v = []
    for z in (-h, h):
        for k in range(lados):
            ang = 2 * math.pi * k / lados
            v += [r * math.cos(ang), r * math.sin(ang), z]
    return v


def quat_yaw(yaw: float) -> list[float]:
    import math
    return [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]


def compilar(cena: dict) -> tuple[mujoco.MjModel, str]:
    spec = montar_spec(cena)
    modelo = spec.compile()
    return modelo, spec.to_xml()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: python3 -m real2sim.cena2mjcf cena.json [saida.xml]")
    m, xml = compilar(carregar_cena(sys.argv[1]))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(xml, encoding="utf-8")
    print(f"ok: {m.nbody} corpos, {m.ngeom} geoms, {m.nu} atuadores")
