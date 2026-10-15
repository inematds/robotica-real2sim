# Codex × Claude × Gemini (ER 2 e Argon) na etapa de visão e plano (14/10/2026)

Mesma foto (`exemplos/mesa-foto/foto.jpg`), mesmo pedido, mesma prova na física. Motores:

- **Codex** pela assinatura: `codex exec -i`, `gpt-6-luna`.
- **Claude** pela assinatura: `claude -p`, `claude-opus-5-5` (`INEMA_CLAUDE_TOPO`).
- **Gemini Robotics-ER 2** pela Gemini API (`gemini-robotics-er-2-preview`), camada gratuita. Teste autorizado pelo dono.
- **Gemini 4 Argon** pela **OpenRouter** (`google/gemini-4-argon`, `--motor openrouter`), teste autorizado pelo
  dono. Pela Gemini API direta não rodou: a chave estava na camada gratuita, onde o Argon tem cota zero
  (`429 RESOURCE_EXHAUSTED`, `limit: 0, model: gemini-4-argon`).

```bash
./r2s.py foto exemplos/mesa-foto/foto.jpg cena.json --pedido "pôr o cubo vermelho na bandeja" --motor claude
GEMINI_API_KEY=... ./r2s.py foto exemplos/mesa-foto/foto.jpg cena.json --motor gemini --modelo gemini-robotics-er-2-preview
OPENROUTER_API_KEY=... ./r2s.py foto exemplos/mesa-foto/foto.jpg cena.json --motor openrouter --modelo google/gemini-4-argon
./r2s.py planejar cena.json "arrume a mesa: tudo que é redondo vai para a bandeja" plano.json --motor claude
```

## Cena (cm; x para frente, y para a esquerda)

| Objeto | Codex | Claude | Robotics-ER 2 | Argon |
|---|---|---|---|---|
| cubo vermelho | 6×6×6 · (48, 48) | 7×7×7 · (33, 25) | 5×5×5 · (33, 22) | 6×6×6 · (33, 21) |
| lata azul | ⌀6×12 · (58, 27) | ⌀7×12 · (37, 10) | ⌀7×12 · (38, 11) | ⌀7×12 · (36, 9) |
| bola de tênis | ⌀7 · (57, 0) | ⌀7 · (37, −4) | ⌀7 · (36, −5) | ⌀7 · (36, −4) |
| bandeja | 27×22×6 · (50, −30) | 18×22×4 · (36, −23) | 18×18×4 · (34, −23) | 15×15×4 · (34, −20) |
| Distância cubo–bandeja | **78 cm** | **48 cm** | **45 cm** | **41 cm** |
| Tempo (foto → cena) | ~9 s | ~28 s | ~14 s | ~7 s |

Conferência pela régua da foto (a folha A4 tem 29,7 cm ≈ 435 px na largura): cubo e bandeja ficam a
uns 45–55 cm um do outro, e a bandeja ocupa ~210 px. **Claude, Robotics-ER e Argon chegaram a cenas
quase iguais e fiéis à foto (o Argon um pouco mais compacto). O Codex abriu demais as distâncias e
aumentou a bandeja.**

## Plano e prova na física (20 variações cada)

| | Codex | Claude | Robotics-ER 2 | Argon |
|---|---|---|---|---|
| Plano | lata → bola | bola → lata | lata → bola | bola → lata |
| Episódios cubo → bandeja (50) | 50/50 | 47/50 (cubo de 7 cm, no limite da garra) | 50/50 | 46/50 (cubo girado 30°) |
| Prova sem vagas | 4/20 (20%) | 16/20 (80%) | 0/20 (0%) | 7/20 (35%) |
| Prova com vagas | **19/20 (95%) aprovado** | 16/20 (80%) reprovado | 16/20 (80%) reprovado | **20/20 (100%) aprovado** |
| Onde falha | a bola cai em cima da lata | a lata alta tomba da bandeja rasa | a bola cai sobre a lata; com vagas, a bandeja de 18 cm aperta | sem vagas, a lata tomba sobre a bola |

## Custo e tokens medidos

Números brutos em [`resultados/comparativo-motores.json`](../resultados/comparativo-motores.json); a tabela em imagem sai de `ferramentas/tabela_motores.py`.


| Motor | Custo | Tokens |
|---|---|---|
| Codex (`gpt-6-luna`) | 0 a mais (assinatura) | foto: 26.760 entrada + 279 saída; plano: 24.741 + 100 (a maior parte da entrada são instruções do próprio Codex) |
| Claude (`claude-opus-5-5`) | 0 a mais (assinatura) | foto: 174.040 entrada (111.596 lidos do cache) + 3.928 saída; plano: 116.476 (20.936 do cache) + 662 (a entrada inclui as instruções do Claude Code) |
| Robotics-ER 2 | **US$ 0** (camada gratuita) | foto: 1.600 entrada (1.080 da imagem) + 433 resposta + 1.538 de raciocínio; plano: 377 + 70 + 1.145 |
| Argon via OpenRouter (**medido**) | **US$ 0,0101** por foto + plano (foto US$ 0,0086; plano US$ 0,0015) | foto: 1.614 entrada + 542 saída; plano: 389 + 72 (sem raciocínio contado à parte) |

## O que isso ensina

- **A cena mais generosa aprova plano que o mundo real reprovaria.** O Codex passou com uma bandeja
  50% maior e mais funda que a real. Nas cenas fiéis do Claude e do ER, a mesma tarefa fica em 80%.
  (Revisto em 15/10: o plano do Codex também passa 20/20 na cena do Claude, então a ordem dos passos
  pesa tanto quanto a bandeja; na menor bandeja, a do Argon, cai para 2/20. Ver [ERRO-DE-MEDIDA.md](ERRO-DE-MEDIDA.md).)
- **O Argon foi o único com cena fiel e plano aprovado** (100% com vagas), o mais rápido (7 s) e
  custou US$ 0,01. Uma rodada só: a diferença para o 80% pode estar na variação, não no modelo.
- O modelo do Google **feito para robótica** (ER 2) mediu tão bem quanto o Claude, na metade do tempo
  e de graça na camada gratuita.
- A prova na simulação pegou um problema físico diferente em cada cena. É por isso que ela existe.
- Próxima correção possível (não feita): deitar a lata antes de soltar, ou escolher a vaga pelo
  tamanho de cada objeto.

Arquivos: `resultados/mesa-foto/claude/`, `resultados/mesa-foto/gemini-robotics-er-2-preview/` e
`resultados/mesa-foto/gemini-4-argon/`
(cena, plano, provas, 50 episódios e `*.uso.json` com os tokens).

## Teste com Fable, Astra e Sol (pedido em 14/10, feito em 15/10/2026)

Resultado em [ERRO-DE-MEDIDA.md](ERRO-DE-MEDIDA.md#quatro-modelos-em-esforço-alto-15102026): os três acertaram a escala nas 9 rodadas; nenhum passa no pior caso.

Rodar a mesma foto e o mesmo pedido em mais dois modelos, **pela assinatura**, com **esforço alto**:

- **Fable 5.1** (`claude-fable-5-1`), via `claude -p --model claude-fable-5-1 --effort high`.
- **GPT-6 Astra** (`gpt-6-astra`), via `codex exec -m gpt-6-astra -c model_reasoning_effort="high"`.

- **GPT-6.1 Sol** (`gpt-6.1-sol`), via `codex exec -m gpt-6.1-sol` (incluído em 15/10).

**Feito em 15/10:** opção `--esforco low|medium|high|xhigh|max` no `r2s.py foto/planejar/tudo`
(Codex e Claude), e o primeiro teste com o mesmo `gpt-6-luna` em esforço médio × alto, 3 rodadas cada
([ERRO-DE-MEDIDA.md](ERRO-DE-MEDIDA.md#o-esforço-de-raciocínio-muda-a-medida-15102026)). O médio
infla tudo 1,6×; o alto acerta o tamanho, mas espreme as distâncias. Para os modelos novos, medir o
erro da cena (bandeja, cubo–bandeja) e rodar `ferramentas/matriz_prova.py`, 3 rodadas por modelo.
