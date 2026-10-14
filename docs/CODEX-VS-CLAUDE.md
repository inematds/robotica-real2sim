# Codex × Claude na etapa de visão e plano (14/10/2026)

Mesma foto (`exemplos/mesa-foto/foto.jpg`), mesmo pedido, os dois pela assinatura (sem API).
Codex: `codex exec -i` com `gpt-6-luna`. Claude: `claude -p` com `claude-opus-5-5` (`INEMA_CLAUDE_TOPO`).

```bash
./r2s.py foto exemplos/mesa-foto/foto.jpg cena.json --pedido "pôr o cubo vermelho na bandeja" --motor claude
./r2s.py planejar cena.json "arrume a mesa: tudo que é redondo vai para a bandeja" plano.json --motor claude
```

## Cena (cm; posição x para frente, y para a esquerda)

| Objeto | Codex: tamanho · posição | Claude: tamanho · posição |
|---|---|---|
| cubo vermelho | 6×6×6 · (48, 48) | 7×7×7 · (33, 25), girado 15° |
| lata azul | ⌀6 × 12 · (58, 27) | ⌀7 × 12 · (37, 10) |
| bola de tênis | ⌀7 · (57, 0) | ⌀7 · (37, −4) |
| bandeja | 27×22×6 · (50, −30) | 18×22×4 · (36, −23), girada −10° |
| Tempo da resposta | ~9 s | ~28 s |

Conferência pela régua da foto (a folha A4 tem 29,7 cm ≈ 435 px na largura): cubo e bandeja ficam a
uns 45–55 cm um do outro. O Claude pôs 48 cm; o Codex, 78 cm. A bandeja de 27 cm do Codex também
fica grande demais para os ~210 px que ela ocupa. O Claude declarou a incerteza com mais detalhe
(x com erro de ±5 cm, porque a borda da mesa não aparece). **Nesta foto, a cena do Claude é mais fiel.**

## Plano e prova na física (20 variações cada)

| | Codex | Claude |
|---|---|---|
| Plano | lata → bola | bola → lata (a bola está mais perto da bandeja) |
| Episódios cubo → bandeja | 50/50 | 47/50 (cubo de 7 cm, quase no limite da garra de 8 cm) |
| Prova sem vagas | 4/20 (20%) reprovado | 16/20 (80%) reprovado |
| Prova com vagas | 19/20 (95%) aprovado | 16/20 (80%) reprovado |
| Onde falha | a bola cai em cima da lata | a lata de 12 cm tomba para fora da bandeja de borda baixa (4 cm) |

## O que isso ensina

- A cena "mais bonita" não é a melhor: a do Codex passou na prova porque a bandeja dele era maior e
  mais funda que a real. Com a medida mais fiel do Claude, a mesma tarefa reprova. **Um gêmeo
  generoso aprova plano que falharia no robô real.**
- A prova pegou um problema físico diferente em cada cena (colisão entre objetos × lata alta em
  bandeja rasa). As duas são o motivo de existir o `r2s.py provar`.
- Próxima correção possível (não feita): deitar a lata antes de soltar, ou pôr a lata no centro e a
  bola na vaga do canto.

Arquivos: `resultados/mesa-foto/claude/` (cena, plano, provas, 50 episódios).
