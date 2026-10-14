# Codex × Claude × Gemini na etapa de visão e plano (14/10/2026)

Mesma foto (`exemplos/mesa-foto/foto.jpg`), mesmo pedido, mesma prova na física. Motores:

- **Codex** pela assinatura: `codex exec -i`, `gpt-6-luna`.
- **Claude** pela assinatura: `claude -p`, `claude-opus-5-5` (`INEMA_CLAUDE_TOPO`).
- **Gemini Robotics-ER 2** pela Gemini API (`gemini-robotics-er-2-preview`), camada gratuita. Teste autorizado pelo dono.
- **Gemini 4 Argon** pela Gemini API: **não rodou.** A chave usada está na camada gratuita e, nela, o
  Argon tem cota zero (`429 RESOURCE_EXHAUSTED`, `generate_content_free_tier_requests, limit: 0,
  model: gemini-4-argon`). Ele só roda num projeto com faturamento ativo.

```bash
./r2s.py foto exemplos/mesa-foto/foto.jpg cena.json --pedido "pôr o cubo vermelho na bandeja" --motor claude
GEMINI_API_KEY=... ./r2s.py foto exemplos/mesa-foto/foto.jpg cena.json --motor gemini --modelo gemini-robotics-er-2-preview
./r2s.py planejar cena.json "arrume a mesa: tudo que é redondo vai para a bandeja" plano.json --motor claude
```

## Cena (cm; x para frente, y para a esquerda)

| Objeto | Codex | Claude | Robotics-ER 2 |
|---|---|---|---|
| cubo vermelho | 6×6×6 · (48, 48) | 7×7×7 · (33, 25) | 5×5×5 · (33, 22) |
| lata azul | ⌀6×12 · (58, 27) | ⌀7×12 · (37, 10) | ⌀7×12 · (38, 11) |
| bola de tênis | ⌀7 · (57, 0) | ⌀7 · (37, −4) | ⌀7 · (36, −5) |
| bandeja | 27×22×6 · (50, −30) | 18×22×4 · (36, −23) | 18×18×4 · (34, −23) |
| Distância cubo–bandeja | **78 cm** | **48 cm** | **45 cm** |
| Tempo (foto → cena) | ~9 s | ~28 s | ~14 s |

Conferência pela régua da foto (a folha A4 tem 29,7 cm ≈ 435 px na largura): cubo e bandeja ficam a
uns 45–55 cm um do outro, e a bandeja ocupa ~210 px. **Claude e Robotics-ER chegaram a cenas quase
iguais e fiéis à foto. O Codex abriu demais as distâncias e aumentou a bandeja.**

## Plano e prova na física (20 variações cada)

| | Codex | Claude | Robotics-ER 2 |
|---|---|---|---|
| Plano | lata → bola | bola → lata | lata → bola |
| Episódios cubo → bandeja (50) | 50/50 | 47/50 (cubo de 7 cm, no limite da garra) | 50/50 |
| Prova sem vagas | 4/20 (20%) | 16/20 (80%) | 0/20 (0%) |
| Prova com vagas | **19/20 (95%) aprovado** | 16/20 (80%) reprovado | 16/20 (80%) reprovado |
| Onde falha | a bola cai em cima da lata | a lata alta tomba da bandeja rasa | a bola cai sobre a lata; com vagas, a bandeja de 18 cm aperta |

## Custo medido

| Motor | Custo | Tokens |
|---|---|---|
| Codex, Claude | 0 a mais (assinatura) | Codex: ~27 mil entrada na foto, ~25 mil no plano (a maior parte são instruções do próprio CLI) |
| Robotics-ER 2 | **US$ 0** (camada gratuita) | foto: 1.600 entrada (1.080 da imagem) + 433 resposta + 1.538 de raciocínio; plano: 377 + 70 + 1.145 |
| Argon (estimado com os tokens do ER) | ~US$ 0,04 por foto + plano (US$ 2/US$ 10 por milhão; raciocínio cobrado como saída) | não medido: cota zero na camada gratuita |

## O que isso ensina

- **A cena mais generosa aprova plano que o mundo real reprovaria.** Só a do Codex passou, porque a
  bandeja dele era 50% maior e mais funda que a real. Nas duas cenas fiéis, a mesma tarefa fica em 80%.
- O modelo do Google **feito para robótica** (ER 2) mediu tão bem quanto o Claude, na metade do tempo
  e de graça na camada gratuita.
- A prova na simulação pegou um problema físico diferente em cada cena. É por isso que ela existe.
- Próxima correção possível (não feita): deitar a lata antes de soltar, ou escolher a vaga pelo
  tamanho de cada objeto.

Arquivos: `resultados/mesa-foto/claude/` e `resultados/mesa-foto/gemini-robotics-er-2-preview/`
(cena, plano, provas, 50 episódios e `*.uso.json` com os tokens).
