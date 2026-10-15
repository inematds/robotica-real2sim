# Erro de medida: o plano passou porque é bom ou porque a cena era generosa?

Pergunta de um leitor do guia (15/10/2026): a prova só sorteia posição, giro e massa, nunca o
**tamanho**. Se o modelo de visão errar a medida, a simulação aprova o erro. Como a bandeja do Codex
saiu 27×22×6 cm, contra uns 18×22×4 nos outros modelos, o 95% dele podia ser falso.

## O que mudou no código

```bash
./r2s.py provar cena.json plano.json --var-tamanho 0.15   # bandeja 0–15% menor e mais rasa, objetos ±7,5%
./r2s.py provar cena.json plano.json --pior-caso          # bandeja 15% menor e objetos 7,5% maiores, sempre
.venv/bin/python ferramentas/matriz_prova.py              # cada ordem de plano × cada cena × 3 modos (~26 s)
```

As vagas continuam calculadas sobre a medida, e só a física usa o tamanho alterado. É o que acontece
de verdade: o robô planeja com o que a câmera mediu e encontra a mesa como ela é. O que a garra pega
nunca passa de 7,8 cm.

## Resultado (20 variações cada, semente 0, 15/10/2026)

Os 4 modelos fizeram só duas ordens de plano: **lata→bola** (Codex, Robotics-ER 2) e **bola→lata**
(Claude, Argon). Cada ordem rodou em cada cena:

| Cena (bandeja) | Plano | Medida | Tamanho ±15% | Pior caso |
|---|---|---|---|---|
| Codex (27×22×6) | lata→bola | 19/20 | 20/20 | 19/20 |
| Codex (27×22×6) | bola→lata | 20/20 | 5/20 | 16/20 |
| Claude (18×22×4) | lata→bola | **20/20** | 17/20 | 1/20 |
| Claude (18×22×4) | bola→lata | 16/20 | 2/20 | 8/20 |
| Robotics-ER 2 (18×18×4) | lata→bola | 16/20 | 12/20 | 1/20 |
| Robotics-ER 2 (18×18×4) | bola→lata | **20/20** | **20/20** | **20/20** |
| Argon (15×15×4) | lata→bola | 2/20 | 1/20 | 0/20 |
| Argon (15×15×4) | bola→lata | 20/20 | 17/20 | 0/20 |

Números brutos: [`resultados/mesa-foto/cruzada/matriz.json`](../resultados/mesa-foto/cruzada/matriz.json).
A linha "Medida" repete os resultados antigos de cada modelo (19, 16, 16 e 20 de 20).

## O que isso ensina

- **A crítica estava certa no essencial, mas a causa não era só a bandeja.** O plano do Codex rodou na
  cena fiel do Claude e passou 20/20. A **ordem** dos passos pesa tanto quanto o tamanho. Agora, na
  menor bandeja plausível (15×15 do Argon), o mesmo plano cai para 2/20.
- **15% de folga não cobre um erro de 50%.** Na cena do Codex, o plano dele passa até no pior caso,
  porque a bandeja ainda fica maior que a real. Variar o tamanho protege contra erro pequeno de medida.
  Contra erro grande, só serve a **prova cruzada** (rodar na cena mais apertada entre os modelos) ou a
  **medida real** com fita métrica.
- **Com erro de medida, quase nada se sustenta.** Só um dos oito pares passa nos três modos:
  bola→lata na bandeja de 18×18. Duas coisas numa bandeja de 15–18 cm com 4 cm de borda, e uma delas
  é uma lata de 12 cm em pé, deixam a tarefa no limite. A correção certa é física (deitar a lata,
  escolher a vaga pelo tamanho do objeto), não um número melhor.
- **Os resultados não sobem nem descem em linha reta** (bola→lata na cena do Codex: 20 → 5 → 16).
  Com 20 tentativas e uma lata alta caindo numa bandeja rasa, a variação entre rodadas é grande.
  Antes de concluir algo de uma linha só, rodar com mais tentativas e outras sementes.

## Regra nova para mandar ao robô real

Um plano só vai para o braço se passar **no pior caso** (`--pior-caso`) **e** na menor bandeja
plausível entre as medidas disponíveis. Com uma foto só, sem medida conferida, nenhum dos quatro planos
de hoje passaria.

## Próximo passo (pendente)

Foto **real** da mesa, com cada objeto medido com fita métrica, quando os braços chegarem. Com isso:
(1) o erro de cada modelo de visão vira número medido, e o 15% chutado é trocado pelo erro real;
(2) o mesmo plano roda no braço físico e dá para comparar a taxa da simulação com a taxa real.
