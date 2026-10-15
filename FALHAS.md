# FALHAS — uma linha por falha (mais recente no topo)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 15/10/2026 | `r2s.py foto` com Astra/Sol (esforço alto) recusava a cena inteira: `tarefa.pegar = "lata_azul, bola_tenis"` (dois objetos num campo de um) | `para_referencial_do_robo` descarta a chave da tarefa com aviso em vez de falhar; teste novo | prompt |
