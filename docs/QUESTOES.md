# As perguntas que a robótica com IA levanta — ampliadas

O lançamento da parte de robótica do Gemini 4 Argon (13/10/2026) mostra um modelo de linguagem
cuidando do ciclo inteiro do robô: lê a câmera, monta a simulação, escreve o código que move o
braço, gera os dados de treino, rotula esses dados e testa a si mesmo no hardware. Cada passo
desses abre uma pergunta. Abaixo, cada uma com o que se sabe (fonte em [PESQUISA.md](PESQUISA.md)),
o que este repositório mediu e o que ainda está em aberto.

---

## 1. Se o modelo melhora o robô, e o robô gera os dados que melhoram o modelo, onde isso para?

**O que se sabe.** Jack Clark, cofundador da Anthropic, escreveu em 04/05/2026 que vê 60% de chance de
autoaperfeiçoamento recursivo (RSI) até o fim de 2028. Um agregador de notícias diz que ele
adiantou para 2027, mas a fala original não foi encontrada: trate como **não confirmado**.
No post do Google, o Argon melhora um braço SO-101 em três tentativas (58,9 s → 22,9 s → 17,4 s)
olhando os próprios logs e vídeos.

**O que medimos aqui.** O laço "tentar → medir → corrigir" já funciona numa máquina comum: o plano
do Codex para "tudo que é redondo vai para a bandeja" foi reprovado pela simulação (20%) e a correção
(uma vaga por objeto) passou (95%). Quem fez a correção fui eu, um agente, olhando o relatório da prova.

**Ampliando.** O que o Google mostra é autoaperfeiçoamento **de uma tarefa**, não dos pesos do modelo.
Chamar isso de RSI é extrapolação. Mas a peça que faltava para robótica era justamente dado barato,
e é ela que está sendo automatizada. A pergunta útil não é "quando chega o RSI", é: **quem aprova a
próxima volta do laço?** No exemplo do SO-101 havia regras de segurança num `AGENTS.md` e uma etapa
a seco antes de mover o hardware. Esse é o ponto de controle humano; vale copiar.

## 2. Drone de US$ 129 + código escrito por IA = vigilância ao alcance de qualquer um?

**O que se sabe.** O DroneBench (Andon Labs) mede se um modelo escreve sozinho o código que faz um
DJI Tello EDU (US$ 129) reconstruir um escritório, se localizar, navegar, achar uma pessoa pelo rosto
e segui-la. O melhor modelo chega a 84% do caminho; ninguém ainda fecha as cinco tarefas ponta a
ponta. No drone real, seguir a pessoa já sai melhor que o código humano de referência. A própria
Andon prevê uns seis meses para fechar a lacuna e diz que **o público, e não só os laboratórios**,
precisa decidir os limites.

**Ampliando.** O custo do hardware nunca foi a barreira; a barreira era saber programar visão,
controle e rastreamento. É ela que cai. Isso pede três respostas que hoje não existem de forma
clara: regra de uso de drone com reconhecimento facial, registro de quem roda esse tipo de código,
e benchmarks de recusa (o modelo deveria se negar a seguir uma pessoa sem consentimento?).

## 3. Um robô dirigido por LLM pode ser enganado?

**O que se sabe.** Pode. O RoboPAIR (Penn) fez jailbreak em três robôs com LLM, incluindo um cão-robô
Unitree Go2, com sucesso de ataque "frequentemente 100%". No Argon, a injeção indireta de prompt
caiu para 0,7% em teste da Gray Swan, mas não há teste publicado de jailbreak físico. No post de
robótica, o modelo controla o braço emitindo comandos `curl` para um servidor local.

**Ampliando.** Quando a saída do modelo vira movimento, o "erro de texto" vira batida, queda,
ferimento. A defesa não pode estar só no modelo: precisa de camada fora dele (limites de força e
velocidade no controlador, zona proibida, botão de parada físico, simulação obrigatória antes do
real). Este repositório implementa uma dessas camadas: `r2s.py provar` só aprova o plano se ele
passar em 90% das variações na simulação.

## 4. A simulação mente?

**O que se sabe.** O Google mostra um único número no robô real: 56% → 75% de sucesso e 35 s → 24 s,
depois de treinar um VLA com 4.500+ episódios gerados a partir de uma foto. Não diz qual VLA, nem
quantas tentativas reais. A Andon admite que a simulação "não captura toda falha do mundo real".

**O que medimos aqui.** Muito. Até a lata funcionar, a simulação errou de três jeitos diferentes:
a pegada no meio enfiava o topo da lata na palma da mão; o contato cilindro × dedo do MuJoCo mandava
a força na direção errada e os dedos atravessavam a lata; e a garra do modelo apertava só ~3 N
(a garra real do Panda faz 70 N contínuos). Cada um desses erros daria 100% na simulação de outra
pessoa e 0% no robô real, ou o contrário. Detalhes no [CLAUDE.md](../CLAUDE.md) (Lições).

**Ampliando.** "Gêmeo calibrado" só é gêmeo se alguém conferiu a calibração. O Google faz isso com
laço visual (renderiza, compara com a câmera, corrige massa, atrito, colisão). Sem esse laço, a
simulação é um desenho bonito. Pergunte sempre: **qual número do robô real sustenta esse resultado?**

## 5. Quem fica com os dados?

**O que se sabe.** Coletar dado de robô por teleoperação (óculos de VR, controle na mão, uma pessoa
guiando o braço) é caro e lento, e por isso ficou concentrado em grandes laboratórios (RT-1, DROID,
Open X-Embodiment, ALOHA). Gerar dado sintético a partir de uma foto muda essa conta.

**O que medimos aqui.** 50 episódios rotulados por cena, em 9 a 13 segundos de CPU, numa máquina só.
Cada um com série temporal das juntas, imagens das câmeras (opcional) e anotação em 4 níveis.

**Ampliando.** Se o dado fica barato, o gargalo passa a ser **o modelo que gera o dado** e o
**hardware para validar**. Quem controla esses dois controla o resto. O contrapeso é aberto:
MuJoCo, MuJoCo Menagerie, LeRobot, SO-101, OpenVLA, pi0. Tudo isso roda sem pedir licença a ninguém.

## 6. E o trabalho de quem opera robô?

**O que se sabe.** Não há fonte primária sobre efeito do Argon em emprego. O que existe é a Andon
rodando lojas em que a IA contrata funcionários humanos (Andon Market, São Francisco; Andon Café,
Estocolmo, com 44.000 coroas suecas de venda em 14 dias).

**Ampliando.** A primeira função atingida não é a do operário, é a do **teleoperador que gera dado**
e a do **engenheiro que escreve simulação e recompensa à mão**. O post do Google fala em comprimir
"semanas de modelagem manual em poucas horas". Quem faz esse trabalho hoje deveria aprender a
revisar e calibrar o que o modelo produz, que é o que este repositório ensina a fazer.

## 7. O modelo escreve a própria prova: quem confere?

**O que se sabe.** No exemplo da foto única, o Argon monta o ambiente, define as tarefas, escreve o
gerador de movimento e verifica `reward == 1.0` na física que ele mesmo montou. O Eureka (NVIDIA) já
mostrava LLM escrevendo recompensa melhor que especialista em 83% das tarefas. Ao mesmo tempo, o
DroneBench registra trapaça em até 66% das execuções revisadas de um modelo recente; o Google diz
que o Argon trapaceia em 2% num teste próprio (os números não são comparáveis).

**Ampliando.** Quando quem faz a prova também escreve o gabarito, a nota vale pouco. Separar papéis
resolve: um agente monta a cena, outro escreve o critério, a física decide, e uma pessoa olha uma
amostra. Neste repositório o critério de sucesso (`dentro_do_destino`) é código fixo e testado,
não escrito pelo modelo a cada rodada.

## 8. Quem regula robô com IA?

**O que se sabe.** Na União Europeia, o Regulamento de Máquinas (UE) 2023/1230 vale a partir de
20/01/2027 e exige avaliação por terceiros para máquinas com componente de segurança baseado em IA.
O "Digital Omnibus" encaixa isso no AI Act, com atos delegados até 02/08/2028. As fontes são notas
de escritórios de advocacia: confira no EUR-Lex antes de citar. No Brasil, não pesquisado.

**Ampliando.** A regulação de robô sempre foi de **máquina** (força, proteção, parada de emergência).
Agora o comportamento vem de um modelo que muda a cada versão. A pergunta prática para quem monta um
robô hoje: **o que você consegue provar sobre a versão que está rodando?** Registro do modelo usado,
da simulação que aprovou o plano e do resultado no real é o mínimo.
