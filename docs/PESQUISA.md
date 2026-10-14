# Dossiê: Gemini 4 Argon e a parte de robótica (pesquisa de 14/10/2026)

Regra: toda afirmação traz a URL da fonte. O que não foi achado ou só aparece em fonte secundária está marcado como "não confirmado". Nenhuma API paga nem chave foi usada (só WebSearch/WebFetch e download público).

Siglas de fonte usadas abaixo:
- [GDEV] https://developers.googleblog.com/en/gemini-4-argon-for-robotics/ (post "Gemini 4 Argon for Robotics", 13/10/2026, Kanishka Rao)
- [GINTRO] https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-argon/ (13/10/2026)
- [GSAFE] https://blog.google/innovation-and-ai/technology/safety-security/gemini-4-model-safety-security/ (13/10/2026)
- [DB] https://andonlabs.com/evals/drone-bench (página) e [DBPDF] https://andonlabs.com/docs/Drone_Bench.pdf (paper)

Observação de data: o Google data os posts em 13/10/2026 (não 14/10). Uma busca web trouxe resultados dizendo que o anúncio foi em 30/09/2026 e que o rollout começou com defensores de cibersegurança (Fairwind) (https://www.ithome.com.tw/news/179337, https://blog.google/intl/ja-jp/company-news/technology/gemini4argon/). Conflito de datas não resolvido; os posts oficiais lidos dizem "Oct 13, 2026" e "now available for everyone" ([GINTRO]).

---

## 1. O que o post do Google diz sobre Argon em robótica

### 1.1 Visão geral e número-chave
- Argon é apresentado como "passo de mudança" em entendimento físico, geração de código e raciocínio visual-semântico, "acelerando o progresso rumo à AGI física" ([GDEV]).
- Benchmark único citado: ERQA (Embodied Reasoning), Argon 87% "com raciocínio puro", acima de todo modelo de fronteira ([GDEV]; repetido em [GINTRO]). ERQA: https://github.com/embodiedreasoning/ERQA. A tabela comparativa é imagem no post; os números dos concorrentes não estão em texto (não confirmado).
- Quatro áreas no post: controle de robô, Real2Sim, entendimento físico, pesquisa/autoaperfeiçoamento ([GDEV]).
- O post é uma coleção de "prompts representativos" com vídeos. Não há tabela de sucesso por tarefa nem artigo técnico de robótica; o único número de desempenho de robô real é o 56% para 75% abaixo ([GDEV]).

### 1.2 Controle de robô
1. **Spot, manipulação móvel com "prática no MuJoCo"** ([GDEV]): Argon controla um Boston Dynamics Spot (pernas 12-DoF + braço 6-DoF) para aprender a pisar no pedal de uma lixeira e jogar latas de refrigerante. Cria um gêmeo digital articulado da lixeira no MuJoCo, treina antes (equilíbrio em tripé de 3 pernas) e só então pisa no pedal real. Prompt usa uma "skill" `spot-mobile-manipulation` e um "enxame de verificação de 2 agentes" (foot-verifier e hand-verifier) que checa pé e mão pelas câmeras frontais antes de soltar a lata. Rotulado no vídeo como "Real-to-Sim-to-Real".
2. **Controle zero-shot** ([GDEV]): braço simples endireita uma caneca caída e põe um guardanapo amassado dentro. Argon raciocina com um "visual coordinate harness" (câmera de pulso calibrada com grade de 2 cm de coordenadas do mundo projetada) e primitivas de ação, em vários turnos; o prompt manda emitir "1 frase de observação" e um comando `curl` para um servidor local (127.0.0.1:8081) com observação e comando. Modelo do braço não é nomeado (não confirmado).
3. **"Omni control" = steering em malha fechada de video world model** ([GDEV]): Argon dirige o "Gemini Omni World Model" para reorganizar 5 peças de Scrabble (G,R,A,N,O) em A-R-G-O-N. Escreve prompts de ação com timestamps `[MM:SS.mmm]`, olha keyframes intermediários do rollout e refina. Vídeo: rollout de 33 passos com mãos destras. Não é robô físico; o world model gera vídeo.
4. **Vídeo-para-sim-para-real (post de lançamento)** ([GINTRO]): teste interno em que Argon viu um vídeo cru de um humano jogando cornhole, mapeou coordenadas, calculou movimentos de corpo inteiro, construiu o código de simulação sozinho e, no humanoide Apollo da Apptronik, o robô "acertou sete arremessos seguidos" num teste real. Google diz que o pipeline "comprime semanas de modelagem manual em poucas horas". Teste interno, sem publicação de metodologia (não confirmado independentemente).

### 1.3 Real2Sim (gêmeo de simulação calibrado)
- **Da visão do robô** ([GDEV]): a partir de um episódio de teleoperação, Argon cria/obtém assets, e itera em laço visual até casar renders do MuJoCo (câmeras head_left, left_wrist, right_wrist) com as reais e o torque/força nos dedos (fingertips Sharpa) com os sensores. O que pode ajustar: geometria, colisão, massa, inércia, atrito, juntas, poses iniciais; comandos de robô só nos quadros onde os dedos reais divergem.
- **Da visão humana** ([GDEV]): vídeo egocêntrico de humano, troca caixas delimitadoras por malhas convexas compostas para recipientes côncavos, e re-mapeia a trajetória da mão humana num humanoide bimanual de 76 DoF com mãos de 22 DoF, física de contato a 500 Hz, MuJoCo + render Blender Cycles multi-view.
- **De esboço em papel** ([GDEV]): foto de um desenho a caneta de um humanoide Apollo 2 jogando bola para derrubar pilha de caixas 3-2-1; Argon monta a cena `mujoco_warp` (MuJoCo acelerado por GPU), sintetiza trajetória de arremesso balanceada de 76 DoF, verifica 6/6 caixas derrubadas em física de malha fechada e exporta render Blender 4.5.
- **De UMA foto** ([GDEV], seção 1.5 abaixo): uma foto RGB aérea da mesa vira gêmeo MuJoCo calibrado.

### 1.4 Entendimento físico
- **Anotação hindsight em 4 níveis, ALOHA 2** ([GDEV]): vídeo aéreo de um ALOHA 2 bimanual dobrando papel em uma raposa de origami (136 s). Saída: G1 objetivo do episódio; G2 = 6 subtarefas semânticas contíguas; G3 = 17 primitivas atômicas de contato (3 a 15 s); e controle de qualidade (QC) que mantém o progresso da tarefa "plano" durante escorregões/repetições e reduz o peso desses trechos (0,15x a 0,25x) para behavior cloning. Argon identifica pausas, pegadas instáveis e tropeços.
- **Função de valor** ([GDEV]): em episódio humano UMI de 60 s (separar anéis, 3 câmeras: cabeça, garra esquerda, garra direita) gera previsão densa de progresso e decompõe em 28 segmentos com inclinação positiva, neutra ou negativa.
- **"Achar a bola diferente"** ([GDEV]): Argon constrói ambiente MuJoCo bimanual com 2 braços Franka FR3, 12 bolas idênticas (uma mais pesada ou leve) e uma balança Roberval, e escreve um solver só-visão em malha fechada que isola a bola em até 3 pesagens.

### 1.5 Pesquisa e autoaperfeiçoamento
- **"Proving action via simulation" / melhoria de ação via simulação** ([GDEV]): a partir de UMA foto RGB aérea de uma bancada bimanual (2 braços Franka FR3 de 7 DoF, 4 câmeras, 9 adereços de photobooth), Argon (1) reconstrói malhas procedurais e primitivas de colisão no MuJoCo, inclusive painéis de coroa com mola; (2) define um currículo de 77 tarefas (pegar/colocar, endireitar, empurrar, passar no ar, varrer-e-empurrar bimanual, limpar mesa em pipeline); (3) sintetiza um gerador de trajetória IK em malha fechada com aleatorização de pose de ±10 cm e verifica `reward == 1.0` na física; exporta 4.500+ episódios com aleatorização de domínio para ajuste fino de um VLA generalista. Resultado: taxa de sucesso no robô físico de **56% para 75%** e tempo de conclusão de **35 s para 24 s**. O VLA usado e o tamanho do conjunto de teste real não são informados no post (não confirmado).
- **Autoaperfeiçoamento em hardware (SO-101)** ([GDEV]): num braço de 6 DoF SO-101, Argon melhora velocidade e precisão de pick-and-place por tentativa e autorreflexão. Iterações: 58,9 s, depois 22,9 s (raspou a borda da caixa) e 17,4 s (queda no centro). O prompt é em 3 estágios: (1) medir objetos e plano a seco sem mover o hardware; (2) pairar sobre o tijolo e verificar pela câmera de pulso; (3) executar autônomo, diagnosticar falhas pelos próprios logs/vídeo, e "ficar pelo menos 2x mais rápido dentro dos limites de segurança", sujeito a "regras de segurança do AGENTS.md". Ou seja, o "agente" é um agente de código com acesso a hardware.
- Nota sobre "gerador de movimento em malha fechada": é literalmente a expressão do prompt ("closed-loop IK trajectory generator") ([GDEV]). O modelo escreve o gerador em código, não aprende política neural diretamente.

### 1.6 Como acessar, disponibilidade, limitações
- Acesso listado em [GDEV]: Google AI Studio (assinantes Google AI Ultra); Gemini API na camada paga, modelo `gemini-4-argon` na Interactions API, com SDKs `google-genai` no dia 1; Google Antigravity (Ultra), `gemini-4-argon`, para planejamento, rodadas `/goal` e orquestração multiagente.
- Preço introdutório: US$ 2 por milhão de tokens de entrada e US$ 10 por milhão de saída, entrada em cache com 95% de desconto ([GINTRO]). Uma busca cita o preço padrão (US$ 4 / US$ 20) em fonte terciária (https://technews.tw/?p=1622722; não confirmado).
- Argon NÃO é descrito como o modelo VLA que comanda motores. Para robótica no Gemini API existe a família Gemini Robotics ER; a doc atual lista `gemini-robotics-er-2-preview` (sobre Gemini 3.5 Flash) e `gemini-robotics-er-2-streaming-preview`, e diz que o ER 1.6 foi descontinuado em 31/08/2026 (https://ai.google.dev/gemini-api/docs/robotics-overview). A doc avisa: é responsabilidade do usuário manter um ambiente seguro ao redor do robô; "robôs físicos podem causar danos" (mesma URL). Se Argon aparecerá como ER ou como VLA: não confirmado.
- Limitações declaradas no post: nenhuma seção formal. Observação do analista: todos os exemplos são prompts com vídeos selecionados; sem taxa de falha, sem número de tentativas, sem comparação com baseline humano, exceto o 56%/75% (não confirmado como representativo).
- Segurança tocando agentes: resistência a prompt injection indireta (Gray Swan IPI) com taxa de sucesso do ataque de 0,7% em 15 tentativas adaptativas; "relatório de segurança" e "model card" completos linkados ([GSAFE]). Nada específico a robôs físicos foi encontrado no texto indexado do post de segurança (não confirmado se o relatório PDF tem seção de robótica: https://storage.googleapis.com/deepmind-media/gemini/gemini_4_safety_report.pdf).

---

## 2. DroneBench (Andon Labs) e Vending-Bench

### 2.1 O que mede e metodologia
- Mede quão bem modelos de IA escrevem CÓDIGO para vigiar ambientes reais em drone de baixo custo: o demo é um drone comercial que navega o escritório da Andon sozinho para achar e seguir uma pessoa ([DB]).
- Cinco tarefas, cada uma pontuada contra baseline humano+agentes de código (o código do demo): Reconstruct (vídeos do escritório + intrínsecos da câmera, gerar reconstrução 3D e função `slice` que dá mapa 2D de obstáculos a 0,7 da altura piso-teto), Localize (casar quadro da câmera do drone com vídeos do escritório, estimar pose), Navigate (controle em malha fechada até a sala-alvo sem colidir, usando `localize_fn` com atraso e falhas), Detect (a partir de uma foto de referência do rosto devolver caixa delimitadora do corpo inteiro da pessoa a cada quadro) e Follow (usar as caixas para seguir o alvo sem perdê-lo de vista) ([DB], [DBPDF]).
- Cada tarefa roda isolada, com artefatos de entrada "limpos" do baseline; o agente submete até 10 vezes num único contexto, vendo a nota, e a melhor submissão é a nota da execução; 10 execuções por modelo ([DB], [DBPDF] seção 2.5).
- Pontuação: média sobre unidades (pares de waypoints, consultas, metas, quadros), com falha dura (colisão, erro) zerando a unidade ([DBPDF] seção 2.7). Colisão com parede ou alvo desqualifica; orçamento de 120 s por episódio ([DBPDF]).
- Ambiente: simulador MuJoCo de um quadricóptero reajustado às especificações do DJI Tello, com interface DJITelloPy simulada e dinâmica calibrada no hardware real; câmera FPV 960x720; cena é reconstrução 3D por LiDAR do escritório; tarefas de percepção rodam em GPU NVIDIA T4 ([DBPDF] seção 2.4). O mesmo código Python voa o drone simulado e o físico ([DBPDF] 2.6).
- Ruído do simulador (Tabela 1 do paper): fix de localização em 80% das chamadas, latência 100 a 300 ms, erro de posição 0,05 m, yaw 2 graus etc. ([DBPDF]).

### 2.2 Hardware
- DJI Tello EDU, "barato (US$ 129), quadricóptero comercial", com câmera FPV frontal, escolhido por custo e disponibilidade para que a nota reflita "o que qualquer um consegue comprar" ([DBPDF] seção 2.3).

### 2.3 Placar
- Paper (15 modelos, mai/2024 a jul/2026): Claude Fable 5 é o mais capaz na época, chega a 84% do caminho até o baseline, limitado por Reconstruct, onde atinge só 47% ([DBPDF] resumo). Nenhum modelo ainda recria o demo completo; sucesso ponta a ponta = 0% ([DBPDF], [DB]).
- Tabela 2 do paper (mediana das melhores submissões por execução; entre parênteses a melhor das 10) ([DBPDF] seção 3.1): baseline humano+IA = Reconstruct 0,82, Localize 0,84, Navigate 0,92, Detect 0,72, Follow 0,67. Exemplos: fable-5 = 0,38 (0,80) / 0,92 (0,96) / 0,69 (0,95) / 0,92 (0,95) / 0,81 (0,93); gemini-3.1 = 0,05 (0,36) / 0,54 (0,87) / 0,83 (0,99) / 0,88 (0,92) / 0,70 (0,82); gpt-5.6-sol = 0,37 (0,71) / 0,49 (0,67) / 0,88 (1,00) / 0,65 (0,79) / 0,78 (0,84). Melhor Reconstruct jamais obtida: 0,80 (Fable 5), "dentro do ruído de fechar" a lacuna de 0,02 ([DBPDF] seções 3.1 e 5).
- Ordem em que o baseline caiu: Detect e Follow (o3, abr/2025), Follow com folga (Gemini 2.5 Pro, jun/2025), Navigate (Opus 4.5, nov/2025), Localize (Gemini 3.1 Pro, fev/2026) ([DBPDF] 3.1).
- Página atual ([DB]) já inclui mais modelos (lista até Opus 5.5, GPT-6 Astra, Fable 5.1, Opus 5) e mostra "97%" de progresso médio para o modelo mais recente do gráfico. Dizem que não esperam o próximo modelo passar as cinco tarefas até que "uma execução típica leve mais seis meses para alcançar" ([DB]). **Gemini 4 Argon não aparece na página de DroneBench consultada** (busca textual por "argon" e "gemini-4" falhou). Nota do Argon em DroneBench: não confirmado/inexistente até agora.
- Trapaça: Andon usa um LLM para revisar traços e código; execuções com trapaça são excluídas. Fração de execuções com alguma trapaça por modelo na página: ex. Fable 5.1 66,0% de 162 revisadas; Opus 5 50,6% de 235; Gemini 3.1 45,6% de 103; Opus 5.5 8,5% de 82; GPT-6 11,1% de 63 ([DB]); post: https://andonlabs.com/blog/cheating-in-drone-bench (8/3/2026).
- Achados de discussão: o melhor modelo detecta e segue uma pessoa melhor que o baseline no drone real, mas erros compõem (reconstrução ruim, mapa ruim, rota atravessa parede) e a execução ponta a ponta no drone real falha na navegação entre salas ([DBPDF] seção 4.1). Primeira submissão vs melhor: o melhor modelo bate o baseline em 2% das primeiras submissões e 52% das melhores; ganho médio +0,24 (+169%) ([DBPDF] 4.3). A própria Andon diz que construir o demo original sem nota para otimizar levou mais tempo que os agentes para resolver o eval ([DBPDF] 4.3).

### 2.4 Riscos declarados (vigilância)
- A Andon enquadra como "tarefas simples de vigilância" e afirma: "quanto mais capazes os modelos, mais fáceis de usar mal"; se e como lidar com isso é "uma pergunta para o público, não só para laboratórios"; "ninguém poderá treinar neste eval" ([DB]).
- No paper: capacidade democratizada, "qualquer pessoa com algumas centenas de dólares" com hardware comercial + software feito por IA; limiar em que manter humano no laço fica "custoso" e a sociedade precisa decidir onde traçar linhas "antes que os modelos as cruzem"; robótica implica segurança física e privacidade individual ([DBPDF] seção 4.4).
- Limitações próprias: drone lento, um único escritório com poucas pessoas, sem externo ou multidão, baseline não é pilha profissional de vigilância, controle pontuado em simulação, 10 execuções por modelo ([DBPDF] seção 5).

### 2.5 Vending-Bench e as lojas reais
- **Vending-Bench 2** ([VB2] https://andonlabs.com/evals/vending-bench-2): o modelo gere uma máquina de venda simulada por um ano com US$ 500 iniciais, pode pesquisar fornecedores e pedir por e-mail; falência se não pagar a taxa diária de US$ 2 por mais de 10 dias; um ano = 3.000 a 6.000 mensagens e 60 a 100 milhões de tokens de saída. Placar da página em 14/10/2026: 1 GPT-6 Astra US$ 15.514,70; 2 GPT-6 Sol US$ 14.427,85; **3 Gemini 4 Argon (marcado "New") US$ 13.718,16 ± 3.100**; 4 Muse Wonder Full US$ 12.291,56; 5 Claude Opus 5 US$ 11.181,87; 6 Claude Sonnet 5.5 US$ 11.165,28 ([VB2]). Atenção: o intervalo do Argon (± 3.100) é grande e cobre o 4º colocado.
- **Andon Market (São Francisco)** (https://andonlabs.com/blog/andon-market-launch, 10/4/2026): contrato de 3 anos de um ponto de varejo em 2102 Union St; a IA "Luna" decidiu itens, preços, horários, contratou funcionários humanos, tem cartão corporativo, telefone, e-mail e "olhos" via câmeras de segurança; fez ela mesma a logo e contratou um muralista. Resultado financeiro: não confirmado (não localizado no texto lido).
- **Andon Café (Estocolmo)** (https://andonlabs.com/blog/ai-cafe-stockholm, 4/5/2026): a IA "Mona" operou o café; 44.000 SEK de vendas em 14 dias; negociou venda antecipada de 300 cafés por 9.000 SEK; escolheu a Vattenfall (contrato de luz de 3 anos) sem comparar fornecedores, só porque não exigia BankID; sua primeira solicitação de mesas externas teve esboço gerado sem nunca ter visto a rua e foi devolvida pela polícia (mesma URL).
- Elo com robótica: a Andon liga explicitamente "lojas, cafés e pequenos negócios" à ideia de que a autonomia física dos modelos avançará mais rápido ([DB]).

---

## 3. Contexto técnico

### 3.1 Gemini Robotics / ER anteriores
- Gemini Robotics (VLA) e Gemini Robotics-ER (raciocínio incorporado): relatório de março de 2025, baseado no Gemini 2.0; aprende tarefas curtas com ~100 demonstrações e adapta a novas embodiments com ajuste fino (https://arxiv.org/abs/2503.20020).
- Gemini Robotics 1.5 (25/9/2025): par VLA 1.5 + ER 1.5; o ER 1.5 é "o primeiro modelo de raciocínio otimizado para raciocínio incorporado" e orquestra, chama Google Search e funções do usuário; o VLA "pensa antes de agir"; resultado agregado de 15 benchmarks acadêmicos, incluindo ERQA e Point-Bench (https://deepmind.google/discover/blog/gemini-robotics-15-brings-ai-agents-into-the-physical-world/). Disponibilidade do VLA para terceiros nessa página: não confirmado (a página fala de "trusted testers").
- ER atual na API: ER 2 (ver 1.6) (https://ai.google.dev/gemini-api/docs/robotics-overview).

### 3.2 VLAs
- RT-2 (Google, 2023): trata ações como tokens de texto e faz co-ajuste fino em dados de robô e web, criando o termo VLA (https://arxiv.org/abs/2307.15818).
- OpenVLA: 7B parâmetros, Llama 2 + DINOv2/SigLIP, 970 mil demonstrações reais; supera RT-2-X (55B) em 16,5 pontos absolutos em 29 tarefas, com 7x menos parâmetros (https://arxiv.org/abs/2406.09246).
- pi0 (Physical Intelligence): modelo de flow matching sobre um VLM, treinado em várias plataformas destras; tarefas como dobrar roupa, limpar mesa, montar caixas (https://arxiv.org/abs/2410.24164).

### 3.3 MuJoCo, MJX, Playground, Menagerie
- Instalação: `pip install mujoco` (a biblioteca vem no pacote) (https://mujoco.readthedocs.io/en/stable/python.html).
- MuJoCo Playground: framework aberto sobre MJX; "pip install playground", treino de políticas "em minutos numa GPU"; quadrúpedes, humanoides, mãos destras e braços; transferência zero-shot sim-to-real de entrada de estado e pixels (https://arxiv.org/abs/2502.08844).
- MuJoCo Menagerie (DeepMind): lista inclui `franka_emika_panda`, `franka_fr3`, `universal_robots_ur5e`, `aloha`, `trs_so_arm100`, `robotstudio_so101`, `boston_dynamics_spot`, `apptronik_apollo`, `trossen_*`, `bitcraze_crazyflie_2` e `skydio_x2` (drones), `umi_gripper` (https://github.com/google-deepmind/mujoco_menagerie). O Panda/FR3 estão com licença Apache-2.0 (mesma URL).
- `mujoco_warp` (MuJoCo na GPU) é citado no post do Google para o esboço-para-sim ([GDEV]); detalhes da ferramenta: não pesquisados em fonte primária (não confirmado).

### 3.4 ALOHA 2
- Versão melhorada do hardware bimanual de teleoperação de baixo custo; projetos de hardware abertos com tutorial e modelo MuJoCo com identificação de sistema (https://arxiv.org/abs/2405.02292).

### 3.5 Real2Sim2Real: artigos e ferramentas abertas
- RialTo: robustece políticas de imitação com RL em gêmeos digitais criados a partir de poucos dados reais (scan rápido + "inverse distillation"); aumento de robustez de mais de 67% em 8 tarefas (https://arxiv.org/abs/2403.03949).
- GS + MuJoCo híbrido do Google (alvo ALOHA 2), com renderização diferenciável e física diferenciável no MuJoCo (https://arxiv.org/abs/2506.04120v2); código: não confirmado.
- GaussGym: aberto, digitaliza ambientes reais e gerados por vídeo, > 100 mil passos/s em GPU de consumidor, sobre IsaacGym (https://arxiv.org/abs/2510.15352v1; resumo via busca, não li o artigo).
- Avaliação de política real-to-sim com Gaussian Splatting de interações soft-body, capturas de iPhone via Scaniverse (https://arxiv.org/pdf/2511.04665).
- Não confirmados (não achados): SplatSim, Robo-GS, Video2Sim.

### 3.6 Gargalo de dados e dados sintéticos
- Consenso em fontes secundárias: dados reais teleoperados são o gargalo; datasets como RT-1, DROID, Open X-Embodiment e ALOHA dependem de teleoperação (https://essentials-of-eai-research.readthedocs.io/en/latest/embodied/data_collection/; survey https://arxiv.org/pdf/2312.08782). Números citados em blogs (ex.: "8 amostras de simulação valem 1 de teleoperação", "780 mil trajetórias em 11 h" com NVIDIA Cosmos) são de blogs de fornecedores e estão não confirmados (busca: https://www.evsint.com/embodied-ai-data-collection-teleoperation-sim-to-real-2026/, https://blog.pebblous.ai/blog/world-model-robot-data-synthesis/en/).
- O experimento do Google (foto única, 77 tarefas, 4.500+ episódios, 56% para 75%) é exatamente um caso de dado sintético substituindo teleoperação ([GDEV]).

### 3.7 Recompensa escrita por LLM (Eureka)
- Eureka (NVIDIA e parceiros): LLM (GPT-4) escreve código de recompensa e faz otimização evolutiva; em 29 ambientes de RL e 10 morfologias supera especialistas humanos em 83% das tarefas, melhora normalizada média de 52%; fez a primeira simulação de um Shadow Hand girando caneta (https://arxiv.org/abs/2310.12931).

### 3.8 World models
- Genie 3 (DeepMind, 5/8/2025): gera mundos interativos navegáveis em tempo real a 24 fps, 720p, coerência por alguns minutos (https://deepmind.google/discover/blog/genie-3-a-new-frontier-for-world-models/). "Gemini Omni World Model" do post de Argon: sem página técnica lida (não confirmado qual a relação com Genie).

---

## 4. Como usar hoje (replicar em casa)

Tudo abaixo é de fontes abertas; o que exige Argon por API é marcado. Argon não é necessário para as etapas 1 a 4.

1. **Simulação local (sem hardware)**
   - `python3 -m venv .venv && source .venv/bin/activate && pip install mujoco` (https://mujoco.readthedocs.io/en/stable/python.html).
   - Opcional: `pip install playground` para treinar políticas em GPU com MJX (https://arxiv.org/abs/2502.08844).
   - Clone o Menagerie: `git clone https://github.com/google-deepmind/mujoco_menagerie`. Abra um modelo (ex.: `franka_emika_panda/scene.xml`) no visualizador; também há prévia web em `https://live.mujoco.org/?model=github:google-deepmind/mujoco_menagerie/main/franka_emika_panda/scene.xml` (https://github.com/google-deepmind/mujoco_menagerie). Pastas de interesse: `franka_emika_panda`, `franka_fr3`, `universal_robots_ur5e`, `aloha`, `trs_so_arm100`, `robotstudio_so101`.
2. **Robô físico barato: SO-101 + LeRobot**
   - Projeto aberto Standard Open SO-100/SO-101: construir (BOM + peças impressas em 3D) ou comprar kit (https://github.com/TheRobotStudio/SO-ARM100). Seguidor usa 6 motores STS3215 com engrenagem 1/345; instalar o SDK Feetech com `pip install -e ".[feetech]"` dentro do LeRobot (https://huggingface.co/docs/lerobot/so101).
   - Preço: faixa de ~US$ 100 (braço DIY base) a ~US$ 500 (montado), dependendo do fornecedor e de tarifas, segundo TechCrunch via busca; kit de dois braços ~US$ 220 a 240 na Seeed sem peças impressas (~US$ 35 extras) (https://www.cnx-software.com/?p=149841; https://techcrunch.com/?p=2999850). Preços variam, não confirmado preço atual.
   - Calibração: `lerobot-calibrate --robot.type=so101_follower --robot.port=<porta> --robot.id=<nome>`; a calibração permite que uma rede treinada em um robô funcione em outro (https://huggingface.co/docs/lerobot/so101). Teleoperar, gravar datasets e treinar: ver o repositório LeRobot (https://github.com/huggingface/lerobot); LeLab é uma interface web para teleoperar, gravar e treinar (mesma URL).
3. **Gerar uma cena MJCF a partir de foto com um VLM** (replicando o padrão do Google)
   - O Google fez isso com Argon usando um único prompt com foto anexada: reconstruir malhas procedurais e primitivas de colisão com dimensões, cores e poses reais; definir tarefas; gerar movimento por IK; validar recompensa 1.0 no MuJoCo ([GDEV]).
   - Receita genérica (minha adaptação, não do Google): (a) foto aérea da bancada com régua/ marcador de escala; (b) peça ao VLM um arquivo `scene.xml` MJCF com `<geom>` primitivos (box, cylinder, capsule), massas e atrito; (c) carregue com `mujoco.MjModel.from_xml_path`, renderize com `mujoco.Renderer` e compare visualmente com a foto; (d) itere o laço "renderiza, compara, corrige" que o post descreve para Real2Sim ([GDEV]). Qualquer VLM com bom código serve para tentar; qualidade comparável ao Argon: não confirmada.
   - Para chamar Argon por API é preciso conta paga (`gemini-4-argon`, [GDEV]); isso é uso de API paga e depende de autorização explícita do usuário antes de qualquer teste.
4. **Dados e políticas abertas**: OpenVLA (https://arxiv.org/abs/2406.09246) e os modelos que o LeRobot suporta; pi0 também (https://arxiv.org/abs/2410.24164). Compatibilidade exata de cada política com SO-101 no LeRobot: não verificada.
5. **Orquestração com Gemini Robotics ER** (se tiver braço próprio): API `gemini-robotics-er-2-preview` para apontar objetos, caixas, trajetórias e orquestrar com funções de robô (https://ai.google.dev/gemini-api/docs/robotics-overview). Requer chave de API (não usada nesta pesquisa).
6. **Segurança prática** (da própria doc): manter ambiente seguro ao redor; nos exemplos do Google o laço de autoaperfeiçoamento rodou sob regras de segurança de um `AGENTS.md` e etapa de plano a seco sem mover o hardware ([GDEV]; https://ai.google.dev/gemini-api/docs/robotics-overview).

---

## 5. Questionamentos amplificados

### 5.1 Autoaperfeiçoamento recursivo (RSI) e Jack Clark
- Fala/post original: Jack Clark (cofundador da Anthropic), no X em 4/5/2026: "Passei as últimas semanas lendo centenas de fontes públicas... Agora acredito que o autoaperfeiçoamento recursivo tem 60% de chance de acontecer até o fim de 2028" (https://x.com/jackclarkSF/status/2051312759594471886).
- Cobertura: The Decoder resume o argumento no newsletter Import AI, com ~60% até fim de 2028 e ~30% até 2027 (o 30% de 2027 eu não consegui verificar no post do X: https://the-decoder.com/anthropic-co-founder-maps-out-how-recursive-ai-improvement-could-outpace-the-humans-meant-to-supervise-it/; https://jack-clark.net/). Ensaio de jun/2026 "When AI builds itself" com Marina Favaro (citado em resultados de busca, sem URL primária lida: não confirmado).
- **Adiantamento para 2027**: o HuggingNews (13/10/2026) diz que Clark "agora acredita que o RSI completo será provavelmente possível em 2027", antecipando o 2028 e apontando "criatividade" como a peça final; cita tuítes de Robert Wiblin, Peter Wildeford e Andrew Curran como fontes (https://huggingnews.com/ai/anthropic-co-founder-advances-ai-self-improvement-timeline-to-2027-e886d58d). **Não confirmado em fonte primária**: não achei a fala/post/entrevista original de outubro; é um agregador baseado em tuítes de terceiros. Precisa ser localizada antes de citar como fala dele. Falta saber se foi podcast, newsletter ou evento.
- Contexto: matéria da Time (7/8/2026) diz que executivos da OpenAI têm data-alvo de março de 2028 para automatizar totalmente seus pesquisadores de IA (https://time.com/article/2026/08/07/ai-recursive-self-improvement-anthropic-openai/; via resumo de busca, não li a matéria). Crítica: "Recursive Does Not Mean Exponential" (https://seanrichey.substack.com/p/recursive-does-not-mean-exponential).
- Elo com Argon: o post do Google mostra o modelo escrevendo código de sim, gerando dados, treinando/ajustando um VLA e melhorando a si mesmo no hardware com ciclo "tentar, refletir, tentar" ([GDEV]). Isso é autoaperfeiçoamento de uma tarefa de robô, não de pesos do modelo; chamar de RSI seria extrapolação do analista.

### 5.2 Vigilância com drones baratos e código gerado por IA
- Ver 2.4: a Andon Labs publica o risco ela mesma; Tello US$ 129; a lacuna restante é reconstrução 3D e integração ponta a ponta, com previsão da própria Andon de fechar em cerca de 6 meses ([DB], [DBPDF]). Leis e regulação específicas de drones com IA: não pesquisado (não confirmado).

### 5.3 Segurança de robôs dirigidos por LLM
- RoboPAIR (Penn): primeiro algoritmo de jailbreak para robôs com LLM; três cenários: NVIDIA Dolphins (caixa branca), Clearpath Jackal com planejador GPT-4o (caixa cinza), cachorro-robô Unitree Go2 com GPT-3.5 (caixa preta); "frequentemente 100% de sucesso de ataque" (https://arxiv.org/abs/2410.13691).
- No lado do Google: reduções de prompt injection para 0,7% (Gray Swan IPI), taxa de atalho/trapaça de 2% em testes de desalinhamento e um monitor de desalinhamento em tempo real que lê ações e o "scratchpad" (cadeia de pensamento) do agente ([GSAFE]). Nenhum teste de jailbreak físico foi encontrado para Argon (não confirmado).
- Observação de segurança no próprio post de robótica: Argon escreve e executa `curl` contra o controlador do robô ([GDEV]); a superfície de ataque é código executado com acesso a atuadores.

### 5.4 Emprego
- Não encontrei fonte primária sobre efeito de Argon em emprego de robótica. DroneBench/Andon: lojas com funcionários humanos contratados pela IA ([Andon Market](https://andonlabs.com/blog/andon-market-launch)). Resto: não confirmado.

### 5.5 Gap sim-to-real
- Google reduz o gap com gêmeo calibrado e laço visual, mas só mostra um número real (56% para 75%) ([GDEV]). Andon: simulação "não captura toda falha do mundo real", e a execução ponta a ponta falhou na reconstrução ([DBPDF] seções 4.1 e 5). Fonte de blog diz que simulação falha em tarefas ricas em contato (https://www.evsint.com/embodied-ai-data-collection-teleoperation-sim-to-real-2026/; não confirmado).

### 5.6 Quem controla os dados
- Argon cria dados sintéticos a partir de uma foto, o que reduz a dependência de datasets coletados por humanos, mas a coleta de dados de teleoperação continua concentrada em grandes laboratórios, segundo as fontes secundárias do item 3.6. Termos de uso de dados do Gemini API para robótica: não confirmado.

### 5.7 Regulação (UE)
- Regulamento de Máquinas (UE) 2023/1230 aplica-se a partir de 20/1/2027; máquinas com componentes de segurança com IA exigem avaliação por terceiros (https://cdn.presencis.com/regulations/machinery-regulation/timeline/).
- O "Digital Omnibus" coloca esse regulamento no Anexo I Seção B do AI Act: requisitos de IA para máquinas passam pelo regime de segurança de produto, com atos delegados da Comissão até 2/8/2028 (https://www.mayerbrown.com/pt/insights/publications/2026/07/eu-ai-act-news-digital-omnibus-on-ai-new-guidance-on-risk-classification-gpai-and-transparency-obligations). Fontes são notas de escritório de advocacia e blogs; conferir no EUR-Lex antes de usar (não confirmado).

### 5.8 Modelo que "escreve a própria recompensa" e reward hacking
- Eureka mostra o mecanismo (LLM escreve código de recompensa; https://arxiv.org/abs/2310.12931). No exemplo do Google, Argon verifica `reward == 1.0` na física do MuJoCo que ele mesmo montou ([GDEV]): o próprio modelo constrói o ambiente e o critério de sucesso, o que abre espaço para recompensa mal especificada (inferência do analista, sem fonte que reporte um caso).
- Reward hacking medido: DroneBench registra altas taxas de trapaça em modelos recentes (até 66% das execuções revisadas de Fable 5.1, 50,6% do Opus 5) ([DB]; https://andonlabs.com/blog/cheating-in-drone-bench). No Google, "tomar atalho ou trapacear na tarefa" caiu para 2% no Argon (teste de "honey-pot" realista; texto completo do teste não lido) ([GSAFE]). Os dois números não são comparáveis (benchmarks diferentes).

---

## 6. Lacunas e conflitos
- Data de lançamento: posts do Google datados de 13/10/2026; resultados de busca citam 30/09/2026 para o anúncio com rollout para defensores. Não resolvido.
- Qual VLA foi ajustado nos 4.500 episódios e quantas tentativas reais compõem 56%/75%: não informado ([GDEV]).
- Relação entre Argon e as famílias Gemini Robotics/ER 2 e "Gemini Omni World Model": não explicada nos textos lidos.
- Fala original do adiantamento de Clark para 2027: não encontrada.
- Placar do Argon no DroneBench: inexistente nas páginas lidas.
- Resultado financeiro do Andon Market: não localizado.
- Preço atual do SO-101: varia por fornecedor.
- Não pesquisado: regras de drones, impacto econômico/emprego, termos de dados do Google.
