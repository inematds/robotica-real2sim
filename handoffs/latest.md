# Handoff — robotica-real2sim (14/10/2026, ~04:05)

## Feito
- Repo `inematds/robotica-real2sim`: código, testes 8/8, docs (PESQUISA, QUESTOES, CODEX-VS-CLAUDE com 4 motores),
  `resultados/comparativo-motores.json` (tokens/custo), `--motor codex|claude|gemini|openrouter`. Último: a1a189c.
- Guia PT/EN/ES com seção `#modelos` (tabela de tokens/custo/prova). QA 360–1920 px ok.
- Portal: 0d387b4, 0845353 (EN/ES), 4cebbf6 (novidade "mesma foto em 4 IAs"); PRO 836ef01.
- Telegram: INEMA.ROBOT 2745 (projeto) e 2770 (4 IAs); INEMA.GOOGLE 2008 (Argon/ER).
- Gemini API: Argon com cota zero na camada gratuita; Argon rodado pela OpenRouter (US$ 0,0101, autorizado). LIMITES.md atualizado.

## Em andamento
- Vídeo refeito (PT/EN/ES), pasta `~/projetos/output/explica-robotica-r2s/` (o antigo explica-NL0yDYXAQ0E foi abandonado).
  Unit `r2s-orquestra` (log `orquestra.log`): envia EN/ES no estúdio → baixa PT/EN/ES → reel em paralelo → v1+v2 de cada
  idioma → `V2_PRONTO <lang> <mp4>`; fim = `ORQUESTRA_FIM`. Não editar o orquestra.sh enquanto roda.
- Reel r7e `~/projetos/reel7etapas/edicoes/2026-10-14-robo-uma-foto` (imagens via Codex; `fazer` dentro do orquestrador,
  log `fazer.log`).

## Próximos passos
1. Conferir folhas de quadros de cada vídeo (PT/EN/ES) e do reel (`build/revisao/folha-*.jpg`).
2. Player no repo: `videos/index.html` (+ en/es) com MP4 720p; link "Assistir ao vídeo" no guia PT/EN/ES; push.
3. Portal: `videoUpdatesData` + `src/data/videos.ts`.
4. ES: `python3 ~/projetos/wifi/fila-espanhol/fila_es.py --add <mp4> --nome ... --contexto ...` (nunca --help).
5. Reel: `python3 reel7etapas.py publicar <pasta>` (bot v3 + lives1); links no inemaytbot.
6. Telegram: vídeo nos tópicos 2770 (INEMA.ROBOT) e 2008 (INEMA.GOOGLE) — o script só cria tópico novo.
7. Bot v3: arquivos 720p; avisar "Terminei".
