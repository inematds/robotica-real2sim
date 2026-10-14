#!/usr/bin/env python3
"""Gera a tabela comparativa dos motores (PT/EN/ES) como HTML 1920x1080 a partir de
resultados/comparativo-motores.json. Depois: node ferramentas/print_tabela.cjs <pasta>."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
D = json.loads((RAIZ / "resultados/comparativo-motores.json").read_text(encoding="utf-8"))

T = {
 "pt": dict(titulo="Mesma foto, quatro modelos", sub="foto → cena no MuJoCo → plano → 20 provas na física · 14/10/2026",
            cols=["Modelo", "Via", "Cubo–bandeja<br><small>real 45–55 cm</small>", "Tempo", "Tokens<br><small>entrada / saída</small>",
                  "Custo", "Prova do plano<br><small>com vagas</small>"],
            assin="assinatura", gratis="grátis", ok="aprovado", no="reprovado",
            nota="Tokens = foto + plano. Codex e Claude contam as instruções do próprio CLI. Na saída do ER entra o raciocínio. Simulação: MuJoCo local, custo zero."),
 "en": dict(titulo="Same photo, four models", sub="photo → MuJoCo scene → plan → 20 physics trials · 2026-10-14",
            cols=["Model", "Access", "Cube–tray<br><small>real 45–55 cm</small>", "Time", "Tokens<br><small>input / output</small>",
                  "Cost", "Plan proof<br><small>with slots</small>"],
            assin="subscription", gratis="free", ok="approved", no="rejected",
            nota="Tokens = photo + plan. Codex and Claude include the CLI's own instructions. ER output includes reasoning. Simulation: local MuJoCo, zero cost."),
 "es": dict(titulo="Misma foto, cuatro modelos", sub="foto → escena en MuJoCo → plan → 20 pruebas en la física · 14/10/2026",
            cols=["Modelo", "Acceso", "Cubo–bandeja<br><small>real 45–55 cm</small>", "Tiempo", "Tokens<br><small>entrada / salida</small>",
                  "Costo", "Prueba del plan<br><small>con espacios</small>"],
            assin="suscripción", gratis="gratis", ok="aprobado", no="reprobado",
            nota="Tokens = foto + plan. Codex y Claude incluyen las instrucciones del propio CLI. La salida del ER incluye el razonamiento. Simulación: MuJoCo local, costo cero."),
}


def fmt(n, lang):
    s = f"{n:,}"
    return s.replace(",", ".") if lang != "en" else s


def html(lang):
    t = T[lang]
    linhas = []
    for m in D["motores"]:
        tk = m["tokens"]
        ent = tk["foto"]["entrada"] + tk["plano"]["entrada"]
        sai = tk["foto"]["saida"] + tk["plano"]["saida"] + tk["foto"].get("raciocinio", 0) + tk["plano"].get("raciocinio", 0)
        if m["custo_usd"] is None:
            custo = t["assin"]
        elif m["custo_usd"] == 0:
            custo = "US$ 0 · " + t["gratis"]
        else:
            custo = f"US$ {m['custo_usd']:.4f}".replace(".", "," if lang != "en" else ".")
        via = m["via"].split(" (")[0]
        dist = m["cena"]["distancia_cubo_bandeja_cm"]
        bom_dist = 41 <= dist <= 55
        prova = m["prova_com_vagas"]
        cls = "ok" if m["aprovado"] and bom_dist else ("warn" if m["aprovado"] else "bad")
        selo = t["ok"] if m["aprovado"] else t["no"]
        linhas.append(f"""<tr><td class="m">{m['motor']}<br><small>{m['modelo']}</small></td><td>{via}</td>
<td class="{'ok' if bom_dist else 'bad'}">{dist} cm</td><td>{m['cena']['tempo_s']} s</td>
<td>{fmt(ent, lang)} / {fmt(sai, lang)}</td><td>{custo}</td><td class="{cls}"><b>{prova}</b> · {selo}</td></tr>""")
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;800&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
body{{margin:0;width:1920px;height:1080px;background:#0c0c10;color:#e9e9ee;font:30px/1.3 Inter,sans-serif;
 display:flex;flex-direction:column;padding:70px 90px;box-sizing:border-box}}
h1{{font:800 66px Sora;margin:0}} h1 b{{color:#FACC15}} .sub{{color:#9a9aa6;font-size:28px;margin:10px 0 40px}}
table{{border-collapse:collapse;width:100%}} th{{font:600 22px Sora;color:#9a9aa6;text-align:left;padding:0 18px 16px;
 text-transform:uppercase;letter-spacing:.04em;vertical-align:bottom}} th small{{text-transform:none;letter-spacing:0;font-size:19px}}
td{{padding:22px 18px;border-top:1px solid #272730;vertical-align:middle}} td small{{color:#9a9aa6;font-size:20px}}
td.m{{font:600 32px Sora}} .ok{{color:#4ade80}} .bad{{color:#f87171}} .warn{{color:#FACC15}}
.nota{{margin-top:auto;color:#9a9aa6;font-size:22px}}
</style></head><body><h1>{t['titulo'].replace('quatro', '<b>quatro</b>').replace('four', '<b>four</b>').replace('cuatro', '<b>cuatro</b>')}</h1>
<div class="sub">{t['sub']}</div><table><tr>{''.join(f'<th>{c}</th>' for c in t['cols'])}</tr>{''.join(linhas)}</table>
<div class="nota">{t['nota']}</div></body></html>"""


if __name__ == "__main__":
    saida = Path(sys.argv[1] if len(sys.argv) > 1 else RAIZ / "guia/assets")
    saida.mkdir(parents=True, exist_ok=True)
    for lang in T:
        (saida / f"tabela-motores-{lang}.html").write_text(html(lang), encoding="utf-8")
    print("ok", saida)
