"""Foto de uma mesa -> cena.json calibrada, usando um modelo de visão.

Motores (os dois pela assinatura, sem API): Codex CLI (`codex exec -i foto`, padrão) ou
Claude Code (`claude -p`, a foto lida pela ferramenta Read) com `motor="claude"`. O modelo devolve objetos com tipo,
tamanho e posição em centímetros; a calibração vem de um objeto de tamanho conhecido na foto
(folha A4 = 21 x 29,7 cm, por padrão). Depois o script converte para o referencial do braço,
que fica no meio da borda da mesa mais próxima da câmera.

Sem Codex? Escreva a cena à mão (exemplos/mesa-teste/cena.json) ou cole o PROMPT abaixo em
qualquer chat com visão e salve a resposta como JSON.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .cena2mjcf import validar_cena

PROMPT = """Você está montando o GÊMEO DE SIMULAÇÃO (MuJoCo) da mesa desta foto para um braço robótico.

Referência de escala: {referencia}. Use-a para estimar os tamanhos reais.
Referencial: origem no MEIO da borda da mesa mais próxima da câmera; x em cm para frente (para
longe da câmera), y em cm para a ESQUERDA de quem tira a foto. Posição = centro da base do objeto.

Para cada objeto que um braço com garra de 8 cm de abertura poderia mover, e para recipientes
(bandeja, caixa aberta, cesto), devolva:
- nome: snake_case curto em português (ex.: cubo_vermelho)
- tipo: "caixa" | "cilindro" | "esfera" | "recipiente"
- tamanho em cm: caixa/recipiente [comprimento_x, largura_y, altura]; cilindro [diametro, altura]; esfera [diametro]
- pos_cm: [x, y]
- yaw_graus: giro em torno do eixo vertical (0 se alinhado com a mesa)
- cor: uma palavra (vermelho, azul, verde, amarelo, laranja, branco, preto, marrom, roxo, cinza, rosa, bege)
- massa_g: estimativa
Ignore a folha de referência e objetos planos (papel, celular deitado).

Também estime a mesa: largura_cm (eixo y) e profundidade_cm (eixo x), e a cor do tampo.
{instrucao}
Responda SOMENTE com JSON válido, sem comentários, neste formato:
{{"mesa": {{"largura_cm": 0, "profundidade_cm": 0, "cor": ""}},
 "objetos": [{{"nome": "", "tipo": "", "tamanho": [], "pos_cm": [0, 0], "yaw_graus": 0, "cor": "", "massa_g": 0}}],
 "tarefa": {{"pegar": "<nome>", "destino": "<nome de um recipiente>", "descricao": "<frase curta>"}},
 "confianca": "<o que ficou incerto>"}}"""

ALCANCE_MIN, ALCANCE_MAX = 0.30, 0.75


def perguntar_codex(foto: Path, prompt: str, modelo: str = "gpt-6-luna", timeout: int = 600) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "resposta.txt"
        cmd = ["codex", "exec", "-m", modelo, "-s", "read-only", "--skip-git-repo-check",
               "-i", str(foto), "-o", str(saida), "-"]
        subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=timeout, cwd=tmp)
        if not saida.exists():
            raise RuntimeError("o Codex não devolveu resposta (confira `codex login`)")
        return saida.read_text(encoding="utf-8")


def modelo_claude() -> str:
    """Modelo Claude da fonte única do ecossistema (~/.config/inema/modelos.env), se existir."""
    env = Path.home() / ".config/inema/modelos.env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.startswith("INEMA_CLAUDE_TOPO="):
                return linha.split("=", 1)[1].strip()
    return "claude-opus-5-5"


def perguntar_claude(prompt: str, foto: Path | None = None, modelo: str | None = None, timeout: int = 600) -> str:
    """Claude Code pela assinatura (`claude -p`); a foto é lida com a ferramenta Read."""
    with tempfile.TemporaryDirectory() as tmp:
        if foto is not None:
            destino = Path(tmp) / ("foto" + foto.suffix.lower())
            destino.write_bytes(foto.read_bytes())
            prompt = (f"Abra a imagem {destino.name} deste diretório com a ferramenta Read e responda sobre ela.\n\n"
                      + prompt)
        cmd = ["claude", "-p", "--model", modelo or modelo_claude(), "--allowedTools", "Read",
               "--output-format", "text"]
        r = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=timeout, cwd=tmp)
        if r.returncode != 0 or not r.stdout.strip():
            raise RuntimeError(f"o Claude não respondeu (confira `claude` logado): {r.stderr[-300:]}")
        return r.stdout


ULTIMO_USO: dict = {}  # tokens da última chamada ao Gemini (para medir custo)


def perguntar_gemini(prompt: str, foto: Path | None = None, modelo: str = "gemini-4-argon",
                     timeout: int = 600) -> str:
    """Gemini API (PAGA, só com autorização do dono). Chave na variável de ambiente GEMINI_API_KEY."""
    import base64
    import os
    import urllib.request
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        raise RuntimeError("defina GEMINI_API_KEY (Gemini API é paga; o padrão do projeto é o Codex)")
    partes = [{"text": prompt}]
    if foto is not None:
        tipo = "image/png" if foto.suffix.lower() == ".png" else "image/jpeg"
        partes.insert(0, {"inline_data": {"mime_type": tipo, "data": base64.b64encode(foto.read_bytes()).decode()}})
    corpo = json.dumps({"contents": [{"role": "user", "parts": partes}]}).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
        data=corpo, headers={"content-type": "application/json", "x-goog-api-key": chave})
    d = json.load(urllib.request.urlopen(req, timeout=timeout))
    ULTIMO_USO.clear()
    ULTIMO_USO.update(d.get("usageMetadata", {}), modelo=modelo)
    return "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"] if not p.get("thought"))


def perguntar(motor: str, prompt: str, foto: Path | None = None, modelo: str | None = None) -> str:
    if motor == "gemini":
        return perguntar_gemini(prompt, foto, modelo or "gemini-4-argon")
    if motor == "claude":
        return perguntar_claude(prompt, foto, modelo)
    if foto is None:
        raise ValueError("perguntar(codex) sem foto: use provar.planejar")
    return perguntar_codex(foto, prompt, modelo or "gpt-6-luna")


def extrair_json(texto: str) -> dict:
    m = re.search(r"\{.*\}", texto, re.S)
    if not m:
        raise ValueError("resposta sem JSON")
    return json.loads(m.group(0))


def para_referencial_do_robo(bruta: dict) -> tuple[dict, list[str]]:
    """cm da foto -> metros do robô; aproxima a cena se algo ficar fora do alcance."""
    avisos = []
    objs = []
    for o in bruta["objetos"]:
        x, y = (v / 100 for v in o["pos_cm"][:2])
        objs.append({"nome": o["nome"], "tipo": o["tipo"], "tamanho": [t / 100 for t in o["tamanho"]],
                     "pos": [x, y], "yaw": round(o.get("yaw_graus", 0) * 3.14159 / 180, 3),
                     "cor": o.get("cor", "cinza"), "massa": round(o.get("massa_g", 100) / 1000, 3)})
    # recua o braço / encolhe a cena até tudo caber no anel de alcance do Panda
    xs = [o["pos"][0] for o in objs]
    dx = max(0.0, ALCANCE_MIN + 0.03 - min(xs)) if xs else 0.0
    if dx:
        avisos.append(f"objetos perto da borda: a cena foi empurrada {dx * 100:.0f} cm para frente")
        for o in objs:
            o["pos"][0] += dx
    raio = max(((o["pos"][0] ** 2 + o["pos"][1] ** 2) ** 0.5 for o in objs), default=0)
    if raio > ALCANCE_MAX:
        k = ALCANCE_MAX / raio
        avisos.append(f"cena maior que o alcance do braço: posições reduzidas a {k:.0%} (tamanhos mantidos)")
        for o in objs:
            o["pos"] = [o["pos"][0] * k, o["pos"][1] * k]
            if (o["pos"][0] ** 2 + o["pos"][1] ** 2) ** 0.5 < ALCANCE_MIN:
                o["pos"][0] += ALCANCE_MIN
    for o in objs:
        o["pos"] = [round(o["pos"][0], 3), round(o["pos"][1], 3)]
        if o["tipo"] != "recipiente" and min(o["tamanho"][:2] if o["tipo"] == "caixa" else o["tamanho"][:1]) > 0.075:
            avisos.append(f"{o['nome']}: mais largo que a garra (8 cm); só pode ser empurrado")
    mesa = bruta.get("mesa", {})
    cena = {"fonte": "foto", "mesa": {"largura": max(mesa.get("largura_cm", 120) / 100, 0.9),
                                      "profundidade": max(mesa.get("profundidade_cm", 80) / 100, 0.7),
                                      "centro_x": 0.5, "cor": mesa.get("cor", "bege")},
            "objetos": objs, "tarefa": bruta.get("tarefa", {}), "confianca": bruta.get("confianca", "")}
    return cena, avisos


def foto_para_cena(foto: str | Path, referencia: str = "uma folha A4 (21 x 29,7 cm)",
                   instrucao: str = "", modelo: str | None = None,
                   motor: str = "codex") -> tuple[dict, list[str], str]:
    foto = Path(foto).resolve()
    texto_instr = f"Tarefa pedida pelo usuário: {instrucao}" if instrucao else \
        "Escolha uma tarefa simples de pegar-e-pôr um objeto dentro de um recipiente."
    resposta = perguntar(motor, PROMPT.format(referencia=referencia, instrucao=texto_instr), foto, modelo)
    bruta = extrair_json(resposta)
    cena, avisos = para_referencial_do_robo(bruta)
    validar_cena(cena)
    return cena, avisos, resposta


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("uso: python3 -m real2sim.foto2cena foto.jpg cena.json [\"instrução\"]")
    cena, avisos, _ = foto_para_cena(sys.argv[1], instrucao=sys.argv[3] if len(sys.argv) > 3 else "")
    Path(sys.argv[2]).write_text(json.dumps(cena, ensure_ascii=False, indent=1), encoding="utf-8")
    for a in avisos:
        print("aviso:", a)
    print(f"ok: {len(cena['objetos'])} objetos -> {sys.argv[2]}")
