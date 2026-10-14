# Handoff — robotica-real2sim (14/10/2026, ~02:55)

Pedido do Nei: repo sobre a parte de robótica do vídeo NL0yDYXAQ0E (Gemini 4 Argon), réplica da
simulação, pesquisa, perguntas ampliadas; publicar no portal; refazer o vídeo (só robótica);
publicar no INEMA.ROBOT do Telegram; avisar no bot.

## Feito
- Repo público `inematds/robotica-real2sim` (código + testes 8/8 + resultados + docs/PESQUISA.md + docs/QUESTOES.md).
- Guia PT/EN/ES no Pages: https://inematds.github.io/robotica-real2sim/guia/ (200 nos 3).
- Portal: `0d387b4` (card + quadro de projetos) e `0845353` (EN/ES em translated-courses); inemabuscas `f6030c1`; PRO `b9a328d`.
- Telegram INEMA.ROBOT: tópico https://t.me/c/2412734678/2745 + MENU (msg 2769).

## Em andamento (segundo plano, não mexer nos scripts rodando)
- `robotica-cadeia-heygen` (systemd --user): espera o finviral liberar o perfil HeyGen, envia 2 blocos pelo
  estúdio, baixa, render v1. Log: `~/projetos/output/explica-NL0yDYXAQ0E/cadeia.log` (fim = `V1_PRONTO`).
- `robotica-cadeia-v2`: espera `V1_PRONTO`, roda v2 (build --strict, render, montagem, 720p).
  Log: `cadeia-v2.log` (fim = `V2_PRONTO <mp4>` ou `FALHA ...`).

## Próximos passos (quando V2_PRONTO)
1. Folha de 11 quadros do `v2/final/robotica-real2sim-pt.mp4` (rosto alheio, texto cortado, sobreposição).
2. Player no repo (`videos/index.html` + MP4 720p) e link "Assistir ao vídeo" no guia PT/EN/ES; push.
3. Portal: `videoUpdatesData` + `src/data/videos.ts` (pôster em public/videos/), `npm test && commit && push`.
4. Telegram: mandar o vídeo no tópico 2745 do INEMA.ROBOT.
5. Bot v3: arquivo 720p (`refazvideo/ferramentas/enviar_bot_v3.mjs`); links no inemaytbot. Sem YouTube (não pedido).
Se `FALHA`: ler o log indicado, corrigir `visual/gerar.py` → `python3 visual/gerar.py` → rodar v2 de novo.
