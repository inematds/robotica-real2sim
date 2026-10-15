# Plano: do gêmeo ao braço real (Hiwonder SO-ARM101)

Plano passo a passo para levar o robotica-real2sim ao braço que vai ser comprado: **Hiwonder AI Robotic
Arm Kit for LeRobot SO-ARM101** (Amazon B0HGDCBWWV, US$ 459,99 em 15/10/2026). Escrito em 15/10/2026.
Tudo que está marcado **[confirmar]** ainda não foi verificado.

**A execução deste plano segue no projeto separado [robotica-so101](https://github.com/inematds/robotica-so101)** (um projeto por robô; este repositório continua com o Panda).

## O que é o kit (página da Amazon, 15/10/2026)

| Item | Valor |
|---|---|
| Braços | 2: **líder** (você move com a mão) e **seguidor** (repete), 12 servos no total |
| Servos | **Hiwonder HX-30HM e HX-10HM**, de barramento, com encoder magnético, 12 V, "30 kg" |
| Carga útil | **200 g** |
| Alcance máximo | **400 mm** (o modelo do MuJoCo dá 468 mm; vale o menor) |
| Estrutura | peças em PLA impressas, já montadas |
| Câmeras | 2: uma no pulso e uma externa |
| Placa | BusLinker V3.0 (USB só para dados, a força vem de fonte separada) |
| Software | compatível com LeRobot, segundo o fabricante |

**Comparação com o gêmeo de hoje.** O simulador usa um Franka Panda, braço industrial de ~85 cm de
alcance e 3 kg de carga. O SO-101 alcança metade disso e carrega 15 vezes menos. Uma lata cheia (370 g)
passa da carga dele. A cena da foto, com a bandeja a ~43 cm da base, fica fora do alcance útil.

## Três riscos que mudam o plano

1. **Driver dos servos [confirmar].** O LeRobot fala com o SO-101 original pelo protocolo dos servos
   **Feetech STS3215** (`so101_follower`, SDK `scservo_sdk`). O kit da Hiwonder usa servos próprios
   (HX-30HM e HX-10HM). O tutorial da própria Hiwonder instala o LeRobot com `pip install -e ".[feetech]"`,
   o que sugere protocolo compatível, mas isso não está escrito em lugar nenhum. **Antes de ligar:**
   procurar no material do kit ou no suporte da Hiwonder se os HX falam o protocolo Feetech; se não
   falarem, usar o fork ou driver deles.
2. **Fontes de tensão.** No kit da Hiwonder, o braço líder usa **5 V** e o seguidor usa **12 V**; o
   tutorial deles avisa que trocar as fontes **queima os servos**. Etiquetar as duas fontes e os dois
   braços antes de tudo.
3. **No real não existe "posição perfeita do objeto".** No simulador, o gerador lê a posição exata do
   objeto a cada passo. No braço real, quem dá a posição é a câmera, e esta sessão mostrou que medida
   errada derruba a prova. Por isso o plano tem uma fase só de **percepção real** (Fase 4).

## Regra de segurança (vale para todas as fases)

- Nada vai ao braço sem passar na prova da simulação **no pior caso** (`provar --pior-caso`).
- Primeiro movimento sempre devagar, com cerca virtual no software (limite de x, y e z que a ponta
  não pode cruzar) e torque limitado.
- Parada de emergência = desligar a fonte de 12 V. A tomada fica ao alcance da mão.
- Nunca deixar o braço rodando sozinho. Ninguém com a mão na área de trabalho.
- Ensaio a seco: motores sem torque, só lendo as posições, antes de qualquer movimento comandado.
- Regras num `AGENTS.md` do projeto, como no exemplo do SO-101 do Google (ver `docs/PESQUISA.md`):
  limites, velocidade máxima, o que o agente pode e não pode fazer sozinho.

## Fases

Cada fase tem um critério de pronto no formato `comando → saída esperada`.

### Fase 0 — Gêmeo do SO-101 no simulador (sem o braço; dá para começar já)

O modelo oficial já está baixado em `vendor/menagerie/robotstudio_so101/` (Apache-2.0).

1. Tirar o Panda "fixo" do código: um arquivo de configuração por robô (`real2sim/robos.py`) com
   modelo, nome das juntas, ponto da garra (`tcp` no Panda, `gripperframe` no SO-101), dedos, garra
   aberta/fechada, postura de casa, alcance, abertura e carga máxima.
2. `cena2mjcf.py`: montar a cena com o SO-101; alcance válido de ~0,12 a 0,35 m (com folga sobre os
   400 mm), mesa menor.
3. `gerador.py`: a cinemática inversa hoje usa 7 juntas e controla posição e orientação completas. O
   SO-101 tem 5 juntas no braço e não consegue as 6 coisas ao mesmo tempo: manter posição e "garra para
   baixo", e deixar o giro do pulso livre.
4. Garra: a abertura do SO-101 vai até ~13 cm no modelo (medido: 8,6–9,0 cm com a junta em 1,0 rad e
   12,7–13,2 cm em 1,75 rad). O "8 cm" que hoje está fixo no prompt da visão e do plano passa a vir
   da configuração do robô.
5. Objetos de até 150 g: bola de tênis (~58 g), cubo de madeira ou espuma de 3–4 cm, lata **vazia**,
   copo de papel, potinho.
6. `exportar.py`: os formatos do LeRobot mudam de 7 juntas + garra para 5 + garra.
7. Testes: os mesmos casos de hoje, para os dois robôs.

Critério: `python3 testes/rodar.py --robo so101` → `TUDO OK`, e
`./r2s.py episodios exemplos/mesa-so101/cena.json /tmp/ep -n 50 --robo so101` → 45/50 ou mais.

### Fase 1 — Mesa real medida com fita métrica (sem ligar motor)

É a pendência mais pedida e não tem risco de hardware.

1. Montar a mesa para o alcance do SO-101: base do braço fixa (grampo ou parafuso), objetos entre 15 e
   35 cm da base, bandeja de 15–20 cm, folha A4 de referência.
2. Medir **cada objeto e cada distância** com fita métrica e régua e anotar em
   `exemplos/mesa-real/medidas.json` (a verdade).
3. Fotografar com a câmera externa do kit, sempre da mesma posição (tripé), em boa luz.
4. Rodar a foto 3 vezes em cada modelo (Astra, Sol, Fable, luna) e calcular o **erro medido** de cada
   um, em tamanho e em posição.
5. Trocar o 15% chutado do `--var-tamanho` pelo erro real do melhor modelo.

Critério: `ferramentas/erro_visao.py exemplos/mesa-real` → tabela com o erro médio e o maior erro de
cada modelo, em cm (o script é novo).

### Fase 2 — Montar, ligar e calibrar

1. Conferir as fontes (5 V no líder, 12 V no seguidor), cabos e IDs dos servos.
2. Resolver o driver (risco 1). Se for Feetech: `pip install -e ".[feetech]"` dentro do LeRobot.
3. `lerobot-find-port` para cada placa e `lerobot-find-cameras` para as duas câmeras.
4. Calibrar o seguidor e o líder (no LeRobot oficial: `lerobot-calibrate --robot.type=so101_follower`
   e `--teleop.type=so101_leader`; **[confirmar]** se valem para o kit da Hiwonder).
5. `lerobot-teleoperate` com o líder: mover devagar e conferir que o seguidor copia.

Critério: teleoperar 5 minutos sem tremor nem servo esquentando, e as juntas lidas no software batendo
com as do modelo (mesmo zero, mesmo sentido).

### Fase 3 — Comparar o gêmeo com o braço (sem objeto)

1. Mandar as mesmas 10 posturas para o braço real e para o simulado e medir onde a ponta da garra fica
   no real (com régua ou com a câmera).
2. Medir o erro da ponta e ajustar no modelo o que estiver diferente: zero das juntas, folga e ganho dos
   servos.

Critério: erro da ponta abaixo de 1 cm nas 10 posturas.

### Fase 4 — Percepção real: a câmera dá a posição

1. Calibrar a câmera externa em relação à base: marcador ArUco na base, ou tocar 4 pontos da mesa com a
   ponta da garra e ligar pixels a centímetros.
2. Pôr marcadores ArUco pequenos (impressos) nos objetos e na bandeja. É o jeito mais barato e confiável
   de ter a posição de cada objeto a cada instante.
3. Ligar a leitura da câmera ao gerador no lugar de `pos_objeto()`. O mesmo laço fechado do simulador
   passa a rodar com a câmera.
4. O modelo de visão (Astra, Fable...) continua dizendo **o que** é cada objeto e montando a cena; a
   **posição fina** vem dos marcadores.

Critério: objeto parado medido 20 vezes → variação abaixo de 5 mm; objeto em 5 lugares conhecidos →
erro abaixo de 1 cm.

### Fase 5 — Primeira prova física (sem IA treinada)

1. Tarefa simples: pegar o cubo e pôr na bandeja.
2. Rodar na simulação do SO-101 com a mesma cena: `provar --pior-caso`. Só segue se passar.
3. No braço: primeiro a seco (sem objeto), depois "pairar" 5 cm acima do objeto e conferir pela câmera
   do pulso, e só então executar. Devagar.
4. 20 tentativas reais, mudando um pouco a posição do objeto a cada vez, como na simulação.
5. Anotar a taxa real ao lado das três taxas da simulação (medida, ±tamanho, pior caso).

Critério: tabela "simulação × real" com 20 tentativas reais; meta inicial de 15/20 no real.

### Fase 6 — Dados e treino com o LeRobot

1. Gravar ~50 episódios **reais** com o líder (`lerobot-record`), a mesma tarefa, com as duas câmeras.
2. Exportar ~50 episódios da **simulação** do SO-101 (`./r2s.py exportar`, já existe para o Panda).
3. Treinar a política ACT (`lerobot-train --policy.type=act`) em três versões: só real, só simulação e
   real + simulação.
4. Avaliar cada versão com 20 tentativas no braço.

Critério: tabela com as 3 versões × 20 tentativas. A pergunta que ela responde: **o gêmeo ajuda?**
(Se "real + simulação" ganhar de "só real" com os mesmos 50 episódios reais, ajuda.)

### Fase 7 — Publicar

Fotos, vídeo, a tabela simulação × real e as medidas da fita métrica no guia PT/EN/ES e no README.
É o dado que as pessoas vão pedir primeiro.

## Ordem e dependências

```
Fase 0 (código)  ─┐
Fase 1 (fita)    ─┼─> Fase 2 (ligar) -> Fase 3 (gêmeo × real) -> Fase 4 (câmera) -> Fase 5 (prova) -> Fase 6 (treino) -> Fase 7
```

As Fases 0 e 1 não precisam do braço: dá para fazer enquanto ele não chega.

## Além da bolinha: o que é útil de verdade

O kit é de **ensino e protótipo** (200 g, 40 cm, PLA), não de produção. Dentro disso, há usos reais:

| Uso | Para quem | Por que cabe no SO-101 | Métrica |
|---|---|---|---|
| **Estudo de viabilidade por foto** | empresa pensando em automatizar | fotografa o posto de trabalho, monta o gêmeo e prova a tarefa **antes** de comprar um braço industrial; o SO-101 só valida o método numa versão pequena | taxa na simulação × taxa no real |
| **Triagem por cor ou tipo** | oficina, maker, escola, agricultura | parafusos, peças, sementes ou peças de LEGO são leves e cabem na garra | peças por minuto, % de acerto |
| **Montar kits pequenos** | loja online, brinde, laboratório | pegar 3–5 itens leves de potes e pôr numa caixinha | kits completos sem erro em 20 |
| **Mostrar a peça para a câmera** | inspeção, catálogo de produto | girar uma peça pequena diante da câmera e fotografar todos os lados | fotos aproveitadas, defeito encontrado |
| **Testar app ou aparelho** | quem desenvolve software ou hardware | apertar botões e tocar tela com caneta, repetindo mil vezes | toques certos por hora |
| **Aula de robótica com IA** | cursos INEMA, escolas | o ciclo inteiro (foto → gêmeo → prova → treino → braço) cabe numa mesa | aluno treinando uma tarefa nova |

**Sugestão para a primeira demo depois da bolinha:** triagem por cor, com 20 peças leves em 3 potes.
Ela usa a câmera de verdade (Fase 4), mostra que a cor vem da visão e a posição vem da medida, e dá um
número claro: taxa real × simulação.

Não serve para: objetos acima de ~150 g, precisão abaixo de 1–2 mm, uso contínuo em fábrica, nem nada
perto de pessoas sem supervisão.

## Fontes

- Página do kit na Amazon (B0HGDCBWWV), lida em 15/10/2026: servos, carga, alcance e câmeras.
- Tutorial da Hiwonder no Hackster ("How to use the Hiwonder LeRobot SO-ARM101 robotic arm"): fontes de
  5 V e 12 V, `pip install -e ".[feetech]"`.
- LeRobot, página do SO-101: https://huggingface.co/docs/lerobot/so101
- NVIDIA, trilha "sim-to-real SO-101": https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/07-calibrating-so101.html
- Modelo MuJoCo: `vendor/menagerie/robotstudio_so101/` (Menagerie, Apache-2.0); alcance e abertura da
  garra medidos nesta sessão.
