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

## O esforço de raciocínio muda a medida? (15/10/2026)

Mesmo modelo (`gpt-6-luna`), mesma foto, mesmo pedido, 3 rodadas em cada esforço
(`./r2s.py foto ... --esforco medium|high`). Referência: as cenas de Claude, Robotics-ER 2 e Argon
(bandeja 15–18 cm, cubo–bandeja 41–48 cm) e a régua A4 da foto (45–55 cm).

| Rodada | Tempo | Cubo | Bandeja | Cubo–bandeja | Melhor plano: medida / ±15% / pior caso |
|---|---|---|---|---|---|
| médio 1 | 8 s | **10 cm** | 27×27×7 | 78 cm | 5 / 5 / 4 de 20 |
| médio 2 | 15 s | **10 cm** | 30×25×6 | 75 cm | 20 / 20 / 18 de 20 |
| médio 3 | 9 s | 8 cm | 28×23×5 | 83 cm | 1 / 1 / 1 de 20 |
| alto 1 | 27 s | 6 cm | 20×16×5 | 27 cm | 16 / 15 / 0 de 20 |
| alto 2 | 17 s | **esqueceu o cubo** | 27×24×7 | – | 20 / 17 / 12 de 20 |
| alto 3 | 26 s | 6 cm | 20×18×5 | 29 cm | 18 / 10 / 0 de 20 |

O plano, nas duas faixas de esforço, saiu igual 4 vezes em 4: lata→bola.
Números brutos: [`resultados/mesa-foto/esforco/`](../resultados/mesa-foto/esforco/) (cenas, planos e
`matriz.json`).

- **Esforço médio erra sempre para o mesmo lado:** tudo 1,6× maior. Os 78 cm da primeira rodada do
  Codex não foram azar. O cubo saiu com 10 cm em duas rodadas, maior que os 8 cm da garra, e a bandeja
  foi parar a ~75 cm da base, perto do limite do braço (80 cm): aí o objeto cai no transporte.
- **Esforço alto acerta o tamanho e erra a distância:** cubo de 6 cm e bandeja de 20 cm (perto das
  outras IAs), mas tudo espremido a ~28 cm, e os objetos se esbarram. Em 1 de 3 rodadas, ele esqueceu
  o cubo e voltou a inflar a bandeja. Demora 2× mais.
- **O plano não muda com o esforço.** Com 2 passos, não há o que pensar a mais. Quem decide se a lata
  tomba é a física.
- **Conclusão:** mais esforço troca o tipo de erro, não acaba com ele. Com uma foto só, a escala é o
  ponto fraco de qualquer modelo. Rodar 3 vezes mostra o tamanho da dúvida: se as rodadas discordam
  muito, a cena não serve para aprovar nada.

## Quatro modelos em esforço alto (15/10/2026)

Mesma foto, mesmo pedido, `--esforco high`, 3 rodadas por modelo, pela assinatura. Referência: régua A4
(cubo–bandeja 45–55 cm) e as cenas de Claude/ER/Argon (bandeja 15–18 cm).

| Modelo | Tempo | Cubo | Bandeja (cm) | Cubo–bandeja | lata→bola na própria cena | Melhor pior caso |
|---|---|---|---|---|---|---|
| `gpt-6-luna` | 17–27 s | 6 cm (1 rodada esqueceu) | 20×16 a 27×24 | **27–29 cm** | 5, 20, 3 de 20 | 1, 12, 0 |
| `gpt-6-astra` | 35–48 s | 6,5–7,5 cm | **16–17 × 17 × 3** | 45–46 cm | 7, 20, 20 | 0, 7, 8 |
| `gpt-6.1-sol` | 46–48 s | 7–7,5 cm | 16–18 × 16–22 × 3–4 | 45–47 cm | 20, 0, 20 | 0, 6, 2 |
| `claude-fable-5-1` | 107–164 s | 5–7 cm | 12–18 × 16–24 × 4 | **47 cm nas 3** | **20, 20, 20** | 13, 1, 2 |

"Melhor pior caso" é o maior número entre as duas ordens de plano, em cada rodada. Os quatro planejaram
igual: lata→bola. Números brutos: `resultados/mesa-foto/esforco/` (`matriz-modelos.json`, cenas,
`plano-astra/sol/fable.json`).

- **Astra, Sol e Fable acertaram a escala nas 9 rodadas** (45–47 cm), e o luna errou nas 6 (médio
  infla, alto espreme). **Trocar de modelo pesou mais que trocar de esforço.**
- **Astra é o mais estável na medida:** bandeja de 16–17 cm nas 3 rodadas, em 35–48 s.
- **Fable é o que mais acerta a física na própria cena** (lata→bola 20/20 nas 3), mas a bandeja variou
  de 12 a 18 cm entre rodadas e leva 2–3 min por foto.
- **Sol aumenta a lata:** 13,5–16,5 cm de altura (a lata tem ~12).
- **Nenhum passa no pior caso** (o melhor foi 13/20). A tarefa (lata alta + bola numa bandeja de
  3–4 cm de borda) está no limite com qualquer medida; o que falta é física (deitar a lata), não modelo.
- Falha nova pega no caminho: Astra e Sol às vezes devolvem dois objetos no campo `tarefa.pegar`, e a
  cena inteira era recusada. Agora vira aviso ([FALHAS.md](../FALHAS.md)).

## Aprendizado prático

1. **Não confie numa rodada só da visão.** Rode a foto 3 vezes (ou em 2 modelos). Discordância grande
   entre rodadas é sinal de medida ruim, antes de qualquer simulação.
2. **Leia os avisos do `r2s.py foto` e confira 3 números à mão** antes de simular. "Mais largo que a
   garra" e "posições reduzidas" apareceram nas 3 rodadas de esforço médio, e as 3 estavam infladas. O
   objeto cabe na garra (≤ 8 cm)? O recipiente tem tamanho plausível? A distância bate com a régua?
3. **Prove no pior caso**, não na medida: `--pior-caso`, e a prova cruzada na menor cena plausível.
4. **Escolha bem o modelo da visão, e só depois o esforço.** Astra, Sol e Fable acertaram a escala;
   o luna errou em médio e em alto. No plano, use o esforço padrão (`medium`): o alto não mudou nada
   e só custa tempo.
5. **A física manda na ordem dos passos:** lata→bola e bola→lata trocam de vencedor conforme a
   bandeja. Teste as duas ordens.
6. **Medida de verdade vence tudo:** uma foto com fita métrica (ou duas fotos de ângulos diferentes)
   vale mais que qualquer troca de modelo ou de esforço.

## Regra nova para mandar ao robô real

Um plano só vai para o braço se passar **no pior caso** (`--pior-caso`) **e** na menor bandeja
plausível entre as medidas disponíveis. Com uma foto só, sem medida conferida, nenhum dos quatro planos
de hoje passaria.

## Próximo passo (pendente)

Foto **real** da mesa, com cada objeto medido com fita métrica, quando os braços chegarem. Com isso:
(1) o erro de cada modelo de visão vira número medido, e o 15% chutado é trocado pelo erro real;
(2) o mesmo plano roda no braço físico e dá para comparar a taxa da simulação com a taxa real.
