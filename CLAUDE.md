# CLAUDE.md — robotica-real2sim

Foto da mesa → gêmeo MuJoCo (Franka Panda do Menagerie) → gerador de movimento em malha fechada →
episódios com variação e anotação em 4 níveis → plano do Codex provado na simulação.

- Rodar: `./instalar.sh` uma vez; depois `./r2s.py <comando>` (re-executa no `.venv` sozinho).
  Teste: `python3 testes/rodar.py` (12 casos, ~1 min, sem rede). Sempre `MUJOCO_GL=egl` sem monitor.
- Modelo de visão e planejador = Codex CLI pela assinatura (`gpt-6-luna`). **Nunca** chamar a API do
  Gemini/Argon nem outra API paga sem autorização explícita do dono.
- Números do README vêm de execuções reais em `resultados/`; ao mudar o gerador, rodar de novo
  `episodios` (-n 50) e `provar` (com e sem `--sem-vagas`), mais `ferramentas/matriz_prova.py` (erro de medida) e atualizar as tabelas (README PT/EN/ES e guia).
- `vendor/` (Menagerie) e `.venv/` não entram no git. MP4 de produção fica em `~/projetos/output/`.
- Commits: autor `inematds <inematds@gmail.com>`.

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule under ## Lessons, so it never happens again.

## Lessons

- IK com atuador de posição do Panda: comando = qpos + dq deixa ~1,6 cm de erro por gravidade; usar comando integrado com anti-windup (|q_cmd − q| ≤ 0,1 rad) e postura de descanso só no espaço nulo (somada direto, ela brigava com a tarefa e a garra parava a 1,1 cm do alvo). (14/10/2026)
- Objeto alto (lata): pegar no máximo 3 cm abaixo do topo; pegando no meio, o topo entrava na palma e a lata não soltava. (14/10/2026)
- Cilindro × caixinhas dos dedos do Panda no MuJoCo devolve normal errada e os dedos atravessam a lata (3 cm de penetração): colisão do cilindro como prisma convexo de 24 lados, visual continua cilindro. (14/10/2026)
- A garra do Menagerie aperta ~3 N (a real faz 70 N): latas de 350 g escorregavam; rigidez 10x (~30 N). Antes de culpar o controle, medir a força da garra. (14/10/2026)
- Torção baixa (`friction[1]` = 0,02) deixa objeto alto girar entre os dedos; 0,06 resolveu. Mexer em solref/solmix dos objetos piorou: não repetir. (14/10/2026)
- Câmera no pulso: o eixo -z da câmera é a direção de visão; conferir um quadro antes de filmar (a primeira saiu preta). (14/10/2026)
- Variar o tamanho em ±15% não pega erro de escala de 50% (o plano do Codex passou no pior caso da própria cena); para saber se a medida enganou, rodar a prova cruzada (`ferramentas/matriz_prova.py`) na menor cena plausível. (15/10/2026)
- Contar "passa nos três modos" com critério explícito (≥ 18/20 em cada modo) e por script, não de olho na tabela: escrevi "1 de 8" quando eram 2. (15/10/2026)
- Deitar a lata: girar 90° deixa o pulso baixo demais e o braço não desce até a bandeja; girar a garra em torno da vertical com a lata na mão faz ela escorregar. 60° em torno do eixo dos dedos funcionou. (15/10/2026)
