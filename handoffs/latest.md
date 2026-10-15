# Handoffs — trabalhos abertos

Cada linha é um assunto em andamento: leia o snapshot do assunto que for continuar. Gravado por handoff-grava.py.

<!-- handoff-indice:inicio -->
- `braco-real-so101` · handoffs/history/2026-10-15T195845Z-braco-real-so101.md · 15/10 16:58
<!-- handoff-indice:fim -->

---

Cópia integral do snapshot mais recente (handoffs/history/2026-10-15T195845Z-braco-real-so101.md):

# Handoff — 2026-10-15 — Lata deitada + plano do braço real SO-ARM101

## Projeto e escopo
robotica-real2sim, raiz ~/projetos/robotica-real2sim. Pedido: correção física de deitar a lata + rodar a matriz; atualizar todos os dados; plano passo a passo para o braço físico que o usuário vai comprar (Hiwonder SO-ARM101, Amazon B0HGDCBWWV) e usos úteis para pessoas e empresas.

## Objetivo atual
Plano entregue (docs/PLANO-SO101.md). A próxima frente é a Fase 0 (gêmeo do SO-101 no simulador) ou a Fase 1 (mesa medida com fita), quando o usuário pedir.

## Estado aceito
- [confirmed] `provar --deitar` / `filmar --deitar` / `matriz_prova.py --deitar`: cilindro mais alto que 2× a borda gira 60° sobre a bandeja e desce deitado; vagas pela largura — real2sim/gerador.py, real2sim/provar.py (marcar_deitar, distribuir_vagas)
- [confirmed] Matriz deitada: bandeja Claude 18×22 passa nas duas ordens (pior caso 19/20); a ER bola→lata piorou; a Argon 15×15 não cabe; pares aprovados nos 3 modos: de 2 para 3 em 8 — resultados/mesa-foto/deitar/
- [confirmed] Corrigido "1 de 8" → "2 de 8" (README PT/EN/ES, guia PT/EN/ES, docs)
- [confirmed] Kit: servos Hiwonder HX-30HM/HX-10HM, 200 g, 400 mm, PLA, 2 câmeras, líder 5 V / seguidor 12 V
- [confirmed] Modelo MuJoCo SO-101 baixado (sparse-checkout) em vendor/menagerie/robotstudio_so101 (vendor fora do git); alcance medido 468 mm, abertura da garra até ~13 cm
- [confirmed] Seção #real no guia PT/EN/ES; episódios refeitos 50/50 (12,4 s e 10,3 s)
- Commits a06a228 e lição em seguida (real2sim); a77570f (wifi)

## Proposto / tentado, não confirmado
- [?] Se os servos HX falam o protocolo Feetech do LeRobot (`so101_follower`) — não confirmado; tutorial Hiwonder usa `.[feetech]`
- [unverified] Comandos `lerobot-calibrate --robot.type=so101_follower` valerem para o kit da Hiwonder

## Decisões e restrições
- 60° (90° inalcançável; giro radial faz a lata escorregar; RADIAL=False fica documentado no código)
- `--deitar` é opcional, não é o padrão: a prova deve escolher entre em pé e deitada, cena por cena
- Plano neste projeto, não em repo separado

## Arquivos alterados
- real2sim/gerador.py, real2sim/provar.py, real2sim/filmar.py, r2s.py, ferramentas/matriz_prova.py, testes/rodar.py (12 casos)
- docs/PLANO-SO101.md (novo), docs/ERRO-DE-MEDIDA.md, docs/HUMANOIDES.md, README*.md, guia/{,en/,es/}index.html, guia/assets/clip-lata-deitada.mp4 e fim-lata-deitada.jpg, CLAUDE.md
- Fora do projeto: `~/projetos/wifi/pendencias.md` — braço escolhido + link do plano

## Memória e regras duráveis tocadas
- CLAUDE.md do projeto: lições da contagem (critério por script) e da lata deitada; 12 testes

## Verificação
- Rodado: `.venv/bin/python testes/rodar.py` → TUDO OK (12)
- Rodado: `matriz_prova.py --deitar` com R2S_INCLINAR=60 e 75 → números nas docs
- Rodado: `r2s.py episodios` nas duas cenas → 50/50
- Rodado: prévia do guia (headless) → render ok
- Não rodado: nada no braço real (não chegou); o protocolo dos servos não foi verificado

## Estado em execução
- Processos em segundo plano: nenhum
- Servidores / portas: nenhum
- Worktrees / branches abertos: nenhum

## Perguntas abertas e adiados
- Aberta: confirmar o driver dos servos HX com a Hiwonder antes da Fase 2
- Adiado: Fases 0–7 do plano

## Próxima ação exata
Se o usuário pedir: Fase 0 (real2sim/robos.py com config Panda/SO-101, cena e IK de 5 juntas), critério `testes/rodar.py --robo so101 → TUDO OK`.

## Mapa de retomada
- `docs/PLANO-SO101.md` — o plano e os riscos
- `docs/ERRO-DE-MEDIDA.md` — resultados de medida, esforço, modelos e lata deitada
- `real2sim/gerador.py` — onde o robô está fixo no Panda
- `vendor/menagerie/robotstudio_so101/so101.xml` — modelo do braço

## Checagem de compartilhamento
- Sem segredos, tokens, cookies, dados pessoais ou endpoints privados: sim
