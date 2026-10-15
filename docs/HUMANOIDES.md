# Real2Sim pode acelerar o treinamento de humanoides?

Sim, e os ganhos já são relevantes. Treinar com simulação e dados sintéticos melhora o desenvolvimento de robôs humanoides: a NVIDIA já mostrou ganhos concretos na geração de dados e no desempenho dos modelos.

Na simulação, várias cópias virtuais do humanoide experimentam movimentos e tarefas em paralelo, sem desgastar o equipamento físico.

> Conferido em 14/10/2026. Onde a fonte não confirmou o texto original, a correção aparece em **Conferência**.

## 1. Os ganhos que já foram medidos

| Medida | Valor | O que significa |
|---|---|---|
| Desempenho do GR00T N1 | **+40%** | dados sintéticos + reais, contra só dados reais |
| Dados gerados | **780 mil** | trajetórias artificiais de movimento em 11 horas |
| Volume equivalente | **6.500 h** | de demonstrações humanas, em duração de movimento |
| Velocidade de geração | **591×** | razão entre 6.500 h de trajetórias e 11 h de geração |

Dados publicados pela NVIDIA em março de 2025. O fator 591× é uma razão de **geração de dados**, não uma aceleração comprovada do treinamento completo.

Isso ataca um problema de base: o humanoide precisa aprender a pegar objetos, movimentar o corpo, manter o equilíbrio, coordenar as mãos e reagir a imprevistos. Ensinar tudo isso só com demonstrações físicas é caro e demorado.

Fontes: [NVIDIA, anúncio do Isaac GR00T N1 (mar/2025)](https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Isaac-GR00T-N1--the-Worlds-First-Open-Humanoid-Robot-Foundation-Model--and-Simulation-Frameworks-to-Speed-Robot-Development/default.aspx) · [NVIDIA Technical Blog, pipeline de movimento sintético](https://developer.nvidia.com/blog/building-a-synthetic-motion-generation-pipeline-for-humanoid-robot-learning).

## 2. Onde isso ajuda mais os humanoides

| Capacidade | Ganho potencial da simulação |
|---|---|
| Aprender a andar | experimentar quedas e terrenos sem quebrar o robô |
| Equilíbrio | simular empurrões, tropeços e cargas diferentes |
| Manipulação | aprender a pegar objetos de vários tamanhos |
| Coordenação das mãos | gerar muitas tentativas de movimentos finos |
| Ambientes novos | preparar comportamentos antes da implantação |
| Segurança | testar situações perigosas virtualmente |

O benefício é maior na locomoção: fazer um humanoide cair milhares de vezes no laboratório seria caro e arriscado. Na simulação, ele repete essas experiências sem danificar nada.

Mas vale separar duas coisas. **Sim2Real** já tem aplicações comprovadas em humanoides. O ciclo **Real2Sim2Real** deste projeto, que reconstrói o ambiente real antes de treinar, ainda não tem uma porcentagem universal mostrando quanto é melhor do que as outras técnicas.

## 3. O dado mais impressionante: caminhada do Unitree G1

**1.620×** — no treino de locomoção do Unitree G1 em terreno irregular no Isaac Lab, numa RTX 4090, cada segundo de computação equivale a cerca de 27 minutos de experiência virtual acumulada.

Esse ganho vem da execução paralela e acelerada de ambientes simulados. Não quer dizer que o robô físico ficou 1.620 vezes mais inteligente, nem que o treinamento inteiro ficou 1.620 vezes mais rápido.

O Isaac Lab treina com **4.096 ambientes paralelos**: milhares de experiências atualizam a mesma política de controle.

**Conferência.** A NVIDIA não publica "1.620×" pronto; é uma conta a partir da tabela de benchmarks do Isaac Lab. Na versão 3.0.0-beta, a tarefa `Isaac-Velocity-Rough-G1-v0` (4.096 ambientes, RTX 4090) treina a cerca de 82 mil passos por segundo; com 0,02 s de simulação por passo, dá ~1.640 s (~27 min) por segundo real. Nas páginas da versão 2.x o mesmo teste aparece com 250 mil passos/s, cerca de 3× mais. O número depende da versão.

Fontes: [Isaac Lab, Performance Benchmarks (v3.0.0-beta)](https://isaac-sim.github.io/IsaacLab/v3.0.0-beta/source/overview/reinforcement-learning/performance_benchmarks.html) · [mesma página na v2.2.1](https://isaac-sim.github.io/IsaacLab/v2.2.1/source/overview/reinforcement-learning/performance_benchmarks.html).

## 4. E no uso prático do humanoide, melhora?

Existem demonstrações reais, ainda limitadas.

Um estudo de 2026 usou o Unitree G1 em oito ações da construção civil, entre elas empurrar e arrastar um carrinho de mão. Cada ação passou primeiro por avaliação em simulação, em dois motores de física (IsaacGym e MuJoCo), antes de qualquer teste no robô.

**Conferência.** O texto original dizia que o G1 reproduziu os oito movimentos no robô real. No artigo, as oito ações entram na avaliação simulação-para-simulação, e só as que passaram foram executadas no G1 físico, para proteger o equipamento e o supervisor. O foco é locomoção de corpo inteiro, não manipulação fina nem autonomia completa na obra. Fonte localizada: [arXiv 2608.01600, Perception-and-action system for humanoid robot task execution in construction](https://arxiv.org/pdf/2608.01600); a versão no ScienceDirect citada no texto original não foi localizada.

Outro sinal: o GR00T N1.6, a nova geração do modelo da NVIDIA (3 bilhões de parâmetros, pré-treinado em mais de 10 mil horas de demonstrações de robô), já tem guia oficial de ponta a ponta com o Unitree G1, incluindo teleoperação, ajuste fino e implantação no robô real.

**Conferência.** O texto original citava avaliações publicadas do N1.6 em humanoides reais, com melhoria sobre a versão anterior. Essa avaliação no G1 real não foi localizada em 14/10/2026; o número público encontrado é de simulação (58% em pegar uma maçã e pôr no prato, benchmark MuJoCo, variação de ±15%). Fontes: [NVIDIA build, GR00T N1.6](https://build.nvidia.com/station/gr00t) · [NVIDIA, repositórios do fluxo GR00T + G1](https://docs.nvidia.com/learning/physical-ai/gr00t-e2e-workflow/latest/resources/repos.html).

## 5. Onde entra o Real2Sim do INEMA?

A oportunidade mais interessante é transformar o sistema numa ferramenta de treinamento para **ambientes específicos**.

Exemplo: ensinar um humanoide a trabalhar numa cozinha. Fotografar ou filmar a cozinha, gerar o gêmeo digital, preparar as tarefas, treinar o humanoide virtual, validar e só então levar ao robô.

O mesmo vale para fábricas, hospitais, hotéis e residências. Mas reconstruir a cozinha não basta: é preciso modelar contatos, objetos articulados (portas, gavetas), sensores e a dinâmica do próprio humanoide.

Uma referência próxima dessa direção é o **Video2Sim2Real** (junho de 2026): adquire habilidades de manipulação a partir de **um único vídeo humano**, monta o gêmeo digital pronto para simulação com modelos de base, refina na simulação e transfere ao robô. Os autores relatam mais de 95% de sucesso em tarefas reais. Fontes: [projeto](https://video2sim2real.github.io/) · [arXiv 2606.08828](https://arxiv.org/abs/2606.08828).

## 6. O que ainda não foi resolvido

O principal problema continua sendo a diferença entre simulação e realidade, o *reality gap*:

- Uma mão virtual segura o copo; a mão física pode escorregar.
- O equilíbrio calculado pode falhar num piso desconhecido.
- Pequenas diferenças de peso, atrito ou atraso dos motores comprometem o movimento.
- Uma política treinada para um corpo pode não funcionar em outro sem adaptação.

Por isso os melhores resultados atuais combinam simulação, dados reais, calibração e testes físicos. Neste repositório, o mesmo princípio aparece em pequena escala: o plano só vale depois de passar por `r2s.py provar`, e uma cena generosa demais (a bandeja do Codex, 50% maior que a real) aprova um plano que falharia no mundo real (ver [ERRO-DE-MEDIDA.md](ERRO-DE-MEDIDA.md): com a bandeja 15% menor e a prova cruzada entre modelos, só 1 de 8 combinações se sustenta).

## Conclusão

O ganho para os humanoides é grande, principalmente na criação de experiências de treinamento: geração de dados virtuais centenas de vezes mais rápida, milhares de simulações em paralelo e melhorias mensuráveis em modelos de controle.

A inovação mais relevante para o INEMA não é competir com o Isaac Lab. É **automatizar a criação do ambiente onde o humanoide vai aprender**: filmar uma fábrica, gerar o gêmeo digital, preparar tarefas, treinar o humanoide virtual, validar o comportamento e transferir o aprendizado ao equipamento físico.

Essa combinação Real2Sim + Sim2Real pode reduzir bastante o esforço para adaptar humanoides a lugares novos.

A pergunta que merece ser investigada agora é mais específica: **quanto custa e quanto tempo leva ensinar uma tarefa nova a um humanoide com Real2Sim2Real, comparado com ensiná-la por demonstrações humanas?** Essa comparação, com a mesma tarefa e o mesmo robô, seria uma evidência muito mais forte do valor do projeto do que números isolados de velocidade de simulação.
