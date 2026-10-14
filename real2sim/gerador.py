"""Gerador de movimento em malha fechada: pegar um objeto e pôr no destino.

A cada passo de controle o gerador LÊ a posição atual do objeto (no robô real seria a
percepção) e recalcula o alvo; a cinemática inversa diferencial transforma o alvo do
pulso em ângulos das 7 juntas. Fases: aproximar, descer, fechar, subir, levar, baixar,
abrir, recuar. Cada fase vira um rótulo da anotação hierárquica.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import mujoco
import numpy as np

QUAT_PARA_BAIXO = np.array([0.0, 0.70711, 0.70711, 0.0])  # garra para a mesa, dedos alinhados a y
GARRA_ABERTA, GARRA_FECHADA = 255.0, 0.0
CASA = np.array([0, 0, 0, -1.57079, 0, 1.57079, -0.7853])


@dataclass
class Fase:
    nome: str
    rotulo: str        # texto da primitiva (nível 3 da anotação)
    subtarefa: str     # nível 2
    max_s: float
    inicio: float = 0.0
    fim: float = 0.0


@dataclass
class Resultado:
    sucesso: bool
    motivo: str
    fases: list[Fase] = field(default_factory=list)
    eventos: list[dict] = field(default_factory=list)
    duracao: float = 0.0


class Gerador:
    def __init__(self, modelo: mujoco.MjModel, dados: mujoco.MjData, pegar: str, destino: str,
                 rng: np.random.Generator | None = None, vaga: tuple[float, float] = (0.0, 0.0)):
        self.m, self.d = modelo, dados
        self.pegar, self.destino = pegar, destino
        self.rng = rng or np.random.default_rng()
        self.tcp = modelo.site("tcp").id
        self.obj = modelo.body(pegar).id
        self.alvo_site = modelo.site(destino + "_alvo").id if _tem_site(modelo, destino + "_alvo") else None
        self.alvo_corpo = modelo.body(destino).id
        self.vaga = np.array([vaga[0], vaga[1], 0.0])  # deslocamento dentro do recipiente
        self.juntas = [modelo.joint(f"joint{i}").id for i in range(1, 8)]
        self.qadr = np.array([modelo.jnt_qposadr[j] for j in self.juntas])
        self.dadr = np.array([modelo.jnt_dofadr[j] for j in self.juntas])
        geom = modelo.geom(pegar + "_geom")
        self.meia_altura = float(modelo.geom_aabb[geom.id][5])  # meia altura (vale para malha também)
        self.dedos = set(_geoms_dos_dedos(modelo))
        self.geom_obj = geom.id
        self.q_cmd = dados.qpos[self.qadr].copy()
        self.topo_acima = 0.03  # quanto do objeto fica acima do ponto da garra

    # ---------- percepção (no real: câmera + estimador de pose) ----------
    def pos_objeto(self) -> np.ndarray:
        return self.d.xpos[self.obj].copy()

    def pos_destino(self) -> np.ndarray:
        R = self.d.xmat[self.alvo_corpo].reshape(3, 3)
        if self.alvo_site is not None:
            return self.d.site_xpos[self.alvo_site].copy() + R @ self.vaga
        return self.d.xpos[self.alvo_corpo].copy() + R @ self.vaga

    def tocando(self) -> int:
        n = 0
        for i in range(self.d.ncon):
            c = self.d.contact[i]
            par = {c.geom1, c.geom2}
            if self.geom_obj in par and par & self.dedos:
                n += 1
        return n

    # ---------- controle ----------
    def ik(self, alvo: np.ndarray, ganho: float = 1.0, amort: float = 1e-2) -> np.ndarray:
        """Um passo de IK diferencial (mínimos quadrados amortecidos) -> alvo de juntas."""
        m, d = self.m, self.d
        jp = np.zeros((3, m.nv)); jr = np.zeros((3, m.nv))
        mujoco.mj_jacSite(m, d, jp, jr, self.tcp)
        erro_p = alvo - d.site_xpos[self.tcp]
        q_site = np.zeros(4)
        mujoco.mju_mat2Quat(q_site, d.site_xmat[self.tcp])
        q_inv = np.zeros(4); mujoco.mju_negQuat(q_inv, q_site)
        q_err = np.zeros(4); mujoco.mju_mulQuat(q_err, QUAT_PARA_BAIXO, q_inv)
        erro_r = np.zeros(3); mujoco.mju_quat2Vel(erro_r, q_err, 1.0)
        J = np.vstack([jp[:, self.dadr], jr[:, self.dadr]])
        e = np.concatenate([erro_p, 0.5 * erro_r])
        J_pinv = J.T @ np.linalg.inv(J @ J.T + amort * np.eye(6))
        dq = J_pinv @ e
        # postura de casa só no espaço nulo: não briga com a posição da garra
        dq += (np.eye(7) - J_pinv @ J) @ (0.05 * (CASA - d.qpos[self.qadr]))
        # comando integrado: acumula a correção, o que zera o erro que a gravidade deixaria
        q = d.qpos[self.qadr]
        dq = np.clip(ganho * dq, -0.05, 0.05)
        # anti-windup: o comando nunca se afasta mais de 0,1 rad da junta real
        self.q_cmd = q + np.clip(self.q_cmd + dq - q, -0.1, 0.1)
        self.q_cmd = np.clip(self.q_cmd, m.jnt_range[self.juntas, 0], m.jnt_range[self.juntas, 1])
        return self.q_cmd

    def mover_para(self, alvo_fn, garra: float, fase: Fase, tol: float, vel: float,
                   gravar, cond_extra=None) -> bool:
        """Persegue um alvo que é recalculado a cada passo (malha fechada)."""
        m, d = self.m, self.d
        dt_ctrl = 0.02
        sub = int(dt_ctrl / m.opt.timestep)
        fase.inicio = d.time
        ref = d.site_xpos[self.tcp].copy()
        while d.time - fase.inicio < fase.max_s:
            alvo = alvo_fn()
            passo = alvo - ref
            dist = np.linalg.norm(passo)
            if dist > vel * dt_ctrl:  # limita a velocidade do ponto de referência
                passo = passo / dist * vel * dt_ctrl
            ref = ref + passo
            d.ctrl[:7] = self.ik(ref)
            d.ctrl[7] = garra
            for _ in range(sub):
                mujoco.mj_step(m, d)
            gravar(fase)
            erro = np.linalg.norm(alvo - d.site_xpos[self.tcp])
            if erro < tol and (cond_extra is None or cond_extra()):
                fase.fim = d.time
                return True
        fase.fim = d.time
        self.ultimo_erro = float(erro)
        return False

    def esperar(self, segundos: float, garra: float, fase: Fase, gravar) -> None:
        fixo = self.d.site_xpos[self.tcp].copy()
        fase.max_s = segundos
        self.mover_para(lambda: fixo, garra, fase, tol=-1, vel=0.5, gravar=gravar)

    def executar(self, gravar=lambda fase: None, altura_seg: float = 0.12) -> Resultado:
        d = self.d
        res = Resultado(False, "")
        acima = np.array([0, 0, altura_seg])
        meia = self.meia_altura
        # pega no máximo 3 cm abaixo do topo: objeto alto não pode entrar na palma da mão
        pega = lambda: self.pos_objeto() + np.array([0, 0, max(meia - self.topo_acima, 0.0)])

        plano = [
            ("aproximar", "ir para cima do objeto", "pegar", 4.0),
            ("descer", "descer até o objeto", "pegar", 3.0),
            ("fechar", "fechar a garra", "pegar", 1.0),
            ("subir", "levantar o objeto", "levar", 2.5),
            ("levar", "transportar até o destino", "levar", 4.0),
            ("baixar", "baixar sobre o destino", "soltar", 3.0),
            ("abrir", "abrir a garra", "soltar", 0.8),
            ("recuar", "recuar para cima", "soltar", 2.0),
        ]
        fases = {n: Fase(n, r, s, t) for n, r, s, t in plano}
        res.fases = list(fases.values())

        alinhado = lambda: np.linalg.norm((pega() - self.d.site_xpos[self.tcp])[:2]) < 0.003
        ok = self.mover_para(lambda: pega() + acima, GARRA_ABERTA, fases["aproximar"], 0.008, 0.45, gravar,
                             cond_extra=alinhado)
        if not ok:
            res.motivo = "não alcançou a posição acima do objeto"; return self._fim(res)
        ok = self.mover_para(pega, GARRA_ABERTA, fases["descer"], 0.006, 0.12, gravar)
        if not ok:
            res.motivo = f"não desceu até o objeto (erro {self.ultimo_erro*100:.1f} cm)"; return self._fim(res)
        self.esperar(0.8, GARRA_FECHADA, fases["fechar"], gravar)
        if self.tocando() < 2:
            res.motivo = "a garra fechou sem segurar o objeto"; return self._fim(res)
        res.eventos.append({"t": round(d.time, 3), "evento": "contato dos dois dedos com o objeto"})

        z0 = self.pos_objeto()[2]
        pega_fixo = d.site_xpos[self.tcp].copy()
        # distância do TCP até a base do objeto, medida na pegada (vale para qualquer altura de pega)
        self.folga_tcp = float(pega_fixo[2] - (self.pos_objeto()[2] - meia))
        self.mover_para(lambda: pega_fixo + acima, GARRA_FECHADA, fases["subir"], 0.015, 0.25, gravar)
        if self.pos_objeto()[2] < z0 + 0.05:
            res.motivo = "o objeto escorregou ao subir"; return self._fim(res)
        res.eventos.append({"t": round(d.time, 3), "evento": "objeto levantado da mesa"})

        sobre = lambda: self.pos_destino() + np.array([0, 0, altura_seg + meia + 0.05])
        ok = self.mover_para(sobre, GARRA_FECHADA, fases["levar"], 0.015, 0.4, gravar)
        if not ok or self.tocando() < 1:
            res.motivo = "perdeu o objeto no transporte"; return self._fim(res)
        baixo = lambda: self.pos_destino() + np.array([0, 0, self.folga_tcp + 0.008])
        self.mover_para(baixo, GARRA_FECHADA, fases["baixar"], 0.012, 0.15, gravar)
        self.esperar(0.6, GARRA_ABERTA, fases["abrir"], gravar)
        alto = d.site_xpos[self.tcp].copy() + np.array([0, 0, 0.15])
        # recua devagar nos primeiros centímetros para não arrastar o objeto junto
        perto = d.site_xpos[self.tcp].copy() + np.array([0, 0, 0.03])
        self.mover_para(lambda: perto, GARRA_ABERTA, fases["recuar"], 0.006, 0.05, gravar)
        inicio_recuo = fases["recuar"].inicio
        self.mover_para(lambda: alto, GARRA_ABERTA, fases["recuar"], 0.02, 0.4, gravar)
        fases["recuar"].inicio = inicio_recuo
        self.esperar(0.6, GARRA_ABERTA, Fase("assentar", "esperar assentar", "soltar", 0.6), gravar)

        if self.dentro_do_destino():
            res.sucesso, res.motivo = True, "objeto dentro do destino"
            res.eventos.append({"t": round(d.time, 3), "evento": "sucesso verificado pela física"})
        else:
            res.motivo = "objeto caiu fora do destino"
        return self._fim(res)

    def dentro_do_destino(self) -> bool:
        p = self.pos_objeto()
        c = self.d.xpos[self.alvo_corpo]
        geoms = [g for g in range(self.m.ngeom) if self.m.geom_bodyid[g] == self.alvo_corpo]
        if not geoms:
            return np.linalg.norm(p[:2] - c[:2]) < 0.05
        R = self.d.xmat[self.alvo_corpo].reshape(3, 3)
        local = R.T @ (p - c)
        base = self.m.geom_size[geoms[0]]
        return abs(local[0]) < base[0] and abs(local[1]) < base[1] and local[2] < 0.12

    def _fim(self, res: Resultado) -> Resultado:
        res.duracao = round(self.d.time, 3)
        return res


def _tem_site(m, nome) -> bool:
    try:
        m.site(nome); return True
    except KeyError:
        return False


def _geoms_dos_dedos(m) -> list[int]:
    ids = []
    for nome in ("left_finger", "right_finger"):
        b = m.body(nome).id
        ids += [g for g in range(m.ngeom) if m.geom_bodyid[g] == b and m.geom_contype[g] | m.geom_conaffinity[g]]
    return ids


def ir_para_casa(m: mujoco.MjModel, d: mujoco.MjData) -> None:
    mujoco.mj_resetDataKeyframe(m, d, 0) if m.nkey else mujoco.mj_resetData(m, d)
    d.ctrl[:7] = d.qpos[:7]
    d.ctrl[7] = GARRA_ABERTA
    mujoco.mj_forward(m, d)
