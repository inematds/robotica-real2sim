# Do gêmeo ao braço: como o robô recebe instruções e aprende

Este documento explica como usar o método deste repositório para ensinar uma tarefa a um robô: o que
entra (foto, fotos ou vídeo), como são os dados, como a instrução chega ao motor, como ele aprende no
mundo real e o passo a passo para quem tem um braço **SO-101**.

## 1. Uma foto basta para a cena; o treino vem das variações

A foto não ensina o movimento. Ela monta o **gêmeo digital** do lugar: mesa, objetos e medidas
(`r2s.py foto`). Quem gera o aprendizado é a simulação: o gerador (`real2sim/gerador.py`) cria dezenas
ou milhares de versões da mesma tarefa, com objetos em posições diferentes, tamanhos, massa e atrito
variando, e grava cada tentativa como um **episódio** (`r2s.py episodios`). Hoje: 50 episódios em cerca
de 9 s, com câmeras opcionais e anotação em 4 níveis.

| Entrada | Para que serve |
|---|---|
| **1 foto** | Mesa simples, tudo à vista. É o caso que já funciona aqui. |
| **3–4 fotos de ângulos diferentes** | Medidas melhores e objetos escondidos. A medida é o que mais erra: no teste, o Codex viu a mesa com 78 cm; a real tem ~50. |
| **Sequência de fotos (antes → meio → depois)** | Tarefa de várias etapas: cada foto é o estado que o robô precisa alcançar. |
| **Vídeo de uma pessoa fazendo** | Ensina o *como*, não só o lugar (linha do Video2Sim2Real: um vídeo humano vira movimento, refinado na simulação). |

## 2. Como a instrução chega ao motor: três camadas

| Camada | O que trafega | Frequência | Neste repositório |
|---|---|---|---|
| **1. Plano** (IA) | Texto ou JSON: "pegar o cubo, levar à bandeja, soltar" | uma vez por tarefa | Codex, Claude ou Gemini escrevem `plano.json` |
| **2. Movimento** | Posição da garra (x, y, z) → ângulo de cada junta (cinemática inversa) | 10–50 vezes/s | o gerador em malha fechada calcula a IK e corrige |
| **3. Motor** | Posição-alvo de cada servo, pela USB/serial até a placa do braço | 100–1.000 vezes/s | no SO-101: servos Feetech num barramento serial |

Dois jeitos de automatizar:

- **Programado (funciona hoje aqui):** a IA escreve o plano, a simulação prova (`r2s.py provar`), o
  computador manda as posições ao braço. Previsível, mas só faz o que foi planejado.
- **Aprendido (política):** uma rede neural roda num laço contínuo: lê câmera e juntas, decide a
  próxima ação, repete. Reage sozinha se o objeto se mexe ou escorrega.

## 3. Como são os dados

Cada tentativa é um episódio: uma sequência de instantes com o que o robô viu e o que fez.

```
episódio 0007 · instrução: "Pôr o cubo vermelho na bandeja cinza."
t=0,00  câmeras: [cima, pulso]  juntas: [0,10, -0,50, 0,80, …]  garra: aberta
        ação → juntas-alvo: [0,12, -0,48, 0,79, …]  garra: aberta
t=0,10  …
t=4,20  … garra: fechada
fim: sucesso = sim
```

No repositório: `resultados/<cena>/episodios/ep_NNNN.npz` guarda a série a 50 Hz (`qpos` 7 juntas,
`ctrl` 8 comandos, `tcp` posição da garra, `obj` posição do objeto, `fase`) e, com `--imagens`, as
câmeras `cima` e `pulso` (128×128, 10 Hz). O `ep_NNNN.json` traz a anotação em 4 níveis (objetivo,
subtarefas, primitivas, eventos), a qualidade (sucesso e motivo) e a variação sorteada.

A política aprende a ligação **o que vejo + onde estou → próxima ação**. O LeRobot guarda isso em
tabelas (estado e ação) e vídeos (câmeras); a seção 6 mostra o export.

## 4. Como fazer o robô aprender na vida real

Do mais simples ao mais avançado:

1. **Demonstração com braço-mestre (o mais usado).** O SO-101 vem em par: você move o braço *líder*
   com a mão, o *seguidor* copia, e tudo é gravado. Com 50–100 demonstrações, uma política como a ACT
   já aprende uma tarefa simples.
2. **Misturar com dados da simulação.** Milhares de episódios sintéticos dão variedade; poucas
   demonstrações reais corrigem a física que a simulação errou (receita que deu +40% no GR00T N1, ver
   [HUMANOIDES.md](HUMANOIDES.md)).
3. **Correção humana durante o uso (DAgger).** O robô tenta, você assume quando ele erra, e a correção
   vira dado novo. É o jeito mais eficiente de melhorar depois de colocar em uso
   (`lerobot-rollout --strategy.type=dagger`).
4. **Ciclo contínuo.** Registrar cada falha no real, somar ao conjunto de dados e treinar de novo. Se a
   falha vier do ambiente, nova foto e ajuste do gêmeo.
5. **Tentativa e erro direto no real (reforço).** Existe, mas é lento, gasta o equipamento e precisa de
   alguém para arrumar a mesa a cada tentativa. Quase todo mundo faz isso na simulação e só ajusta no real.

**Regra que não muda:** política nova passa primeiro pela prova na simulação. No real, o braço roda
com limite de força e velocidade, zona proibida e parada física. Se o modelo erra ou é enganado, a
proteção fora dele segura.

## 5. Passo a passo: eu tenho um SO-101, o que faço?

Comandos do LeRobot 0.6.1 (conferidos no pacote). Troque as portas e os nomes pelos seus.

**O que precisa ter**

- O par **SO-101 líder + seguidor** montado (o líder é o que você move com a mão), as duas placas de
  controle e as fontes.
- **1 ou 2 câmeras USB** (uma de frente e, se der, uma no punho do braço).
- Um computador com Linux, macOS ou Windows. Para treinar, uma GPU ajuda muito (ou treine na nuvem).
- Uma mesa fixa, boa luz e os objetos da tarefa.

**Passo 1 — Instalar**

```bash
python3 -m venv .venv-lerobot
.venv-lerobot/bin/pip install "lerobot[feetech,core-scripts,training]"
```

**Passo 2 — Achar as portas e configurar os motores** (uma vez, com cada braço)

```bash
lerobot-find-port                       # desconecte e reconecte quando pedir: mostra a porta de cada braço
lerobot-setup-motors --robot.type=so101_follower --robot.port=/dev/ttyACM0
lerobot-setup-motors --teleop.type=so101_leader  --teleop.port=/dev/ttyACM1
```

**Passo 3 — Calibrar** (cada braço; siga as posições que o comando pede)

```bash
lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=seguidor
lerobot-calibrate --teleop.type=so101_leader  --teleop.port=/dev/ttyACM1 --teleop.id=lider
```

**Passo 4 — Testar o controle** (mexa o líder: o seguidor copia)

```bash
lerobot-find-cameras
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=seguidor \
  --robot.cameras="{ frente: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=/dev/ttyACM1 --teleop.id=lider --display_data=true
```

**Passo 5 — Fazer o gêmeo da sua mesa** (este repositório)

```bash
./r2s.py foto mesa.jpg cena.json          # 2–3 fotos ajudam; confira as medidas com uma trena
./r2s.py episodios cena.json sintetico/ -n 1000 --imagens
./r2s.py exportar sintetico/ dataset-sintetico/   # formato LeRobot (seção 6)
```

O braço da simulação ainda é o Franka Panda: para o dado sintético servir direto ao SO-101, falta
trocar o modelo pelo SO-101 do MuJoCo Menagerie (próximo passo do roteiro). Até lá, o sintético
serve para testar o fluxo e treinar a visão.

**Passo 6 — Gravar demonstrações reais** (50 a 100, variando a posição dos objetos)

```bash
lerobot-record \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=seguidor \
  --robot.cameras="{ frente: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=/dev/ttyACM1 --teleop.id=lider \
  --dataset.repo_id=voce/cubo-na-bandeja --dataset.num_episodes=50 \
  --dataset.single_task="Pôr o cubo vermelho na bandeja cinza." --dataset.push_to_hub=false \
  --display_data=true
```

**Passo 7 — Treinar uma política (ACT)**

```bash
lerobot-train --dataset.repo_id=voce/cubo-na-bandeja --policy.type=act \
  --output_dir=outputs/act-cubo --policy.device=cuda --policy.push_to_hub=false
```

**Passo 8 — Rodar no braço, começando devagar** (mão perto da tomada)

```bash
lerobot-rollout --strategy.type=base --policy.path=outputs/act-cubo/checkpoints/last/pretrained_model \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=seguidor \
  --task="Pôr o cubo vermelho na bandeja cinza." --duration=30
```

**Passo 9 — Corrigir e melhorar.** Rode com `--strategy.type=dagger` para assumir com o líder quando
ele errar; as correções viram episódios novos. Treine de novo.

**Passo 10 — Medir.** Taxa de acerto em 20 tentativas para três políticas: só sintético, só real e
real + sintético. Essa comparação mostra quanto o Real2Sim economiza de demonstração humana.

## 6. Como exportar os episódios para o LeRobot

O LeRobot fica numa venv separada (a do MuJoCo não muda):

```bash
./instalar.sh --lerobot                    # .venv-lerobot com lerobot[dataset]==0.6.1 e torch de CPU
./r2s.py episodios exemplos/mesa-foto/cena.json resultados/mesa-foto/episodios-imagens -n 50 --imagens
./r2s.py exportar resultados/mesa-foto/episodios-imagens resultados/mesa-foto/lerobot
```

Medido em 14/10/2026 (ARM64, CPU), dados em `resultados/mesa-foto/lerobot-export.json`:

| Item | Valor |
|---|---|
| Episódios gerados / com sucesso | 50 / 50, em 30 s |
| Exportação | 69 s → 50 episódios, 4.361 quadros a 10 Hz, 9,7 MB |
| `observation.state` | 7 juntas do Panda |
| `action` | 7 juntas-alvo + garra |
| Câmeras | `cima` e `pulso`, 128×128, em vídeo |
| Conferência | o `LeRobotDataset` abre de volta; a imagem decodificada difere da original 2,3/255 em média (compressão); o estado é idêntico |

Como o exportador funciona (`real2sim/exportar.py`):

- Usa a API oficial (`LeRobotDataset.create` → `add_frame` → `save_episode` → `finalize`), nunca o
  formato escrito à mão.
- O gerador grava o estado a 50 Hz e as câmeras a 10 Hz; o LeRobot exige tudo no mesmo quadro, então o
  dataset sai a 10 Hz, com estado e ação nos mesmos passos das fotos.
- Por padrão só entram os episódios com sucesso; `--com-falhas` inclui todos.
- Sem `--imagens`, o dataset sai só com estado e ação a 50 Hz (vale para testar, mas a ACT precisa das câmeras).

Para treinar com ele: `lerobot-train --dataset.repo_id=local/real2sim --dataset.root=resultados/mesa-foto/lerobot --policy.type=act ...`
(o braço ainda é o Panda: o dado só vale para o SO-101 depois de trocar o modelo na simulação).
