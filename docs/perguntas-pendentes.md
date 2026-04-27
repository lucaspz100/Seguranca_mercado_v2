# Perguntas Pendentes para o Supermercado Kan

Esta é a lista de itens que ainda não temos resposta e que afetam a implementação. Quando você (Claude Code) esbarrar em qualquer um destes pontos durante a implementação, **não invente** — marque com `# TODO(KAN): ...` e prossiga com um valor padrão razoável.

Após a reunião com o Kan, atualizar este arquivo movendo itens para a seção "Respondidas" abaixo.

---

## Bloco 1 — Operação dos seguranças e operadores

1. Os seguranças têm rádio HT, celular institucional, ou apenas celular pessoal? Como recebem comunicação dos operadores hoje?
2. Quantos seguranças em cada turno e onde ficam posicionados (entrada, salão, caixas)?
3. Qual o protocolo atual quando os operadores veem alguém "estranho" pelas câmeras?
4. Em média, quanto tempo um cliente fica na loja? (Define horizonte máximo de tracking necessário.)

## Bloco 2 — Watchlist e responsabilidade

5. **Quem é o responsável formal pela watchlist?** Gerente da loja? Chefe de segurança? Precisa ser uma pessoa nominal com autoridade para incluir e excluir pessoas.
6. Qual o critério hoje para considerar alguém "suspeito conhecido"? Foi pego no flagrante? Foi visto em câmera depois de um furto descoberto? Há registro escrito de cada caso?
7. Existe prazo de permanência na lista, ou é "para sempre"?
8. As fotos atuais dos ~50 suspeitos: foram tiradas em qual condição? (Frame da câmera de entrada? Foto de RG? Câmera interna?) Podemos ter acesso a uma amostra para avaliar qualidade?

## Bloco 3 — Material para treinamento do sistema

9. **Existem vídeos preservados de furtos passados** na loja? Se sim, quantos incidentes aproximadamente, e por quanto tempo o NVR retém vídeo?
10. A partir do início do contrato, o Kan se compromete a marcar e preservar cada novo incidente de furto detectado?
11. Existe alguma documentação ou histórico de comportamentos típicos observados? ("A maioria esconde em mochila", "geralmente trocam embalagem na seção X", etc.)

## Bloco 4 — Protocolo de abordagem (jurídico)

12. **Hoje, quando suspeitam de alguém, qual é o procedimento?** Seguem observando até o caixa? Abordam antes de sair? Chamam polícia?
13. O Kan tem assessoria jurídica fixa que pode validar o protocolo de abordagem baseado em alerta do sistema?
14. Existe sinalização atual sobre videomonitoramento na loja? Eles aceitam adicionar sinalização específica sobre análise biométrica e comportamental?

## Bloco 5 — Infraestrutura técnica

15. **Especificações exatas do servidor:** modelo, CPU, RAM, GPU (se houver), sistema operacional, espaço em disco livre. Pedir um print do gerenciador de tarefas ou `systeminfo` (Windows) / `lscpu` + `nvidia-smi` (Linux).
16. O servidor é **dedicado** ao SINC ou compartilhado com outros sistemas (ERP, gravação, etc.)?
17. Modelo do NVR/DVR Intelbras e modelo das câmeras (ex: VIP 1230 D, iM5, etc.). Resolução e FPS configurados.
18. As câmeras estão em VLAN separada da rede administrativa e da rede de clientes (wifi)?
19. Banda de internet do servidor e da loja.
20. Quem é o responsável pela TI da loja? Funcionário interno ou empresa terceirizada?

## Bloco 6 — Notificações e UX

21. Os seguranças e operadores aceitam instalar um app no celular institucional para receber notificações? Ou preferem WhatsApp/Telegram/SMS?
22. Os operadores hoje usam vídeo wall fixo, monitor giratório, ou cada um tem PC com cliente Intelbras? Onde o dashboard do SINC vai aparecer fisicamente?

## Bloco 7 — Contrato e expectativas

23. Qual a expectativa de prazo para o MVP funcionar nas 2 câmeras de entrada?
24. Qual a expectativa de prazo para cobertura das 300 câmeras?
25. **Qual o critério de sucesso para o Kan?** "Reduzir furtos em X%"? "Pegar Y pessoas/mês"? Sem métrica acordada, projeto não tem fim definido.
26. Manutenção pós-implantação: SLA de resposta a falhas? Frequência de retreino do modelo comportamental?

---

## Respondidas

> Conforme as respostas chegarem, mover os itens de cima para cá com a resposta abaixo do número.

(vazio até agora — atualizar após reunião)
