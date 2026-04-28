# SINC — Sistema Inteligente de Notificação e Captura

> Este arquivo é lido automaticamente pelo Claude Code em toda sessão. Mantém as decisões arquiteturais, princípios e restrições do projeto. **Não remover sem motivo.**

## O que é o SINC, em uma frase

Sistema de visão computacional que recebe streams RTSP de ~300 câmeras Intelbras já instaladas no Supermercado Kan, processa cada frame com modelos de IA (reconhecimento facial contra watchlist, análise comportamental, Re-ID multi-câmera), e gera alertas para operadores humanos validarem.

## Princípios não-negociáveis

1. **Humano no laço.** Nenhum endpoint do sistema dispara ação física automaticamente. Todo alerta espera confirmação humana antes de notificar segurança ou registrar evento durável.
2. **Minimização de dados.** O default é **descartar**. Embeddings de pessoas que não dão match contra a watchlist são descartados em RAM em menos de 1 segundo. Persistência é exceção, não regra.
3. **Degradação graciosa.** Falha de componente não derruba o sistema. Falha de tracking é reportada honestamente ao operador (status alta/média/baixa/perdida), nunca escondida.
4. **Auditabilidade total.** Toda decisão (humana ou de sistema) gera log estruturado e/ou entrada em `audit_log`. Tabela `audit_log` é append-only — sem UPDATE/DELETE permitidos.
5. **Modularidade.** Cada componente (detector, embedder, tracker) é substituível sem reescrita. Comunicação via Redis Streams / Pub-Sub e contratos Pydantic bem-definidos.

## Arquitetura em 5 camadas

- **Camada 1 — Filtro Facial.** ArcFace contra watchlist fechada (~50 pessoas). Ativa apenas em câmeras de entrada/saída.
- **Camada 2 — Análise Comportamental.** RTMPose + regras explícitas. Ativa em câmeras de salão. Reconhecidamente imatura tecnologicamente.
- **Camada 3 — Tracking Dirigido.** OSNet ativado **APENAS** para indivíduos já flaggados pelas Camadas 1 ou 2. **Nunca** para clientes comuns.
- **Camada 4 — Validação Humana.** Dashboard React + notificação móvel para segurança.
- **Camada 5 — Persistência.** PostgreSQL apenas para eventos confirmados.

## Stack tecnológica fixada

- **Backend:** Python 3.11, FastAPI, Uvicorn, SQLAlchemy 2 + Alembic
- **Banco:** PostgreSQL 16, Redis 7
- **Visão computacional:** YOLOv11n (Ultralytics), YuNet (OpenCV), InsightFace `buffalo_l` (ArcFace), Torchreid `osnet_x1_0`, MMPose RTMPose-m, ByteTrack, FAISS
- **Frontend:** React 18 + TypeScript + Vite + Tailwind + shadcn/ui + TanStack Query + Zustand
- **Infra:** Docker + Docker Compose, Ubuntu Server 24.04 LTS
- **Observabilidade:** Prometheus + Grafana + Loki + structlog
- **Notificação móvel:** FCM ou Telegram Bot
- **Auth:** JWT (access 1h, refresh 7d), Argon2id para senhas

## Restrições importantes do contexto

- **Câmeras:** todas Intelbras, fixas, RTSP. Servidor central potente disponibilizado pelo Kan (especificações exatas a confirmar).
- **Watchlist:** ~50 pessoas, fotos vindas das próprias câmeras + outras fontes. Responsável nominal pela watchlist a definir com Kan.
- **Operadores:** 2 pessoas, atuando enquanto a loja está aberta. Tempo de resposta no pior caso > 2 minutos — arquitetura de tracking deve degradar graciosamente nesse horizonte.
- **Comportamento prioritário:** "esconder na roupa/mochila" é o caso primário do Detector B (pose de ocultação).
- **Cloud Intelbras:** existente mas não tem API útil; vamos puxar RTSP direto das câmeras ou via NVR local.
- **LGPD:** validação jurídica em andamento por escritório contratado pelo Kan. Não tomar decisões legais aqui.

## Estrutura do projeto

Ver [`docs/implementacao.docx`](docs/implementacao.docx), Seção 2.2, para árvore completa. Resumo:

```
sinc/
├── docker-compose.yml
├── pyproject.toml
├── docs/                  ← documentação (este arquivo + os docx)
├── infra/                 ← config Postgres, Prometheus, Grafana, Loki
├── models/                ← baixados via script, NÃO versionar
├── sinc/                  ← pacote Python principal
│   ├── ingest/            ← captura RTSP
│   ├── pipeline/          ← detectores, embedders, tracker, behavior/
│   ├── matching/          ← FAISS + tracking ativo
│   ├── alerts/            ← gerência e notificação
│   ├── api/               ← FastAPI + WebSocket
│   ├── db/                ← SQLAlchemy + migrations
│   ├── workers/           ← jobs (retenção, backup, métricas)
│   └── utils/
├── frontend/              ← React + TS + Vite
├── mobile/                ← React Native (app do segurança)
├── scripts/               ← download_models, calibrate_threshold, benchmark
└── tests/                 ← unit, integration, fixtures/videos
```

## Como você (Claude Code) deve trabalhar neste projeto

- **Leia os documentos antes de implementar componentes principais.** `docs/implementacao.docx` tem pseudocódigo de referência para a maioria dos módulos. Use-o como ponto de partida, não copie cego — adapte para os contratos reais.
- **Sempre escreva tipagem.** Pydantic para schemas de API e eventos internos; type hints completos em funções; mypy passando.
- **Sempre escreva logs estruturados** com `structlog`. Padrão: `logger.info("evento.acao", campo1=x, campo2=y)`.
- **Testes acompanham código.** Toda função de lógica de negócio (máquina de estados, filtros, matching) tem teste unitário. Componentes de pipeline têm teste de integração com vídeo de bancada.
- **Migrations sempre versionadas com Alembic.** Nunca alterar schema em produção sem migration.
- **Nada de browser storage no frontend.** Estado em memória + TanStack Query para cache de queries.
- **Antes de adicionar dependência nova,** justifique. A stack está fixada acima; novidades passam por revisão.
- **Não trate de LGPD por conta própria.** Quando uma decisão tocar em retenção, base legal, direitos de titulares, comente no PR e espere review humano.
- **Ainda não sabemos várias coisas sobre o ambiente do Kan.** Ver `docs/perguntas-pendentes.md`. Quando a implementação esbarrar numa dessas perguntas, **não invente** — marque com `# TODO(KAN): ...` e siga.

## Convenções de código

- **Python:** Black para formatação, Ruff para lint, mypy para tipagem.
- **Imports:** ordenados (stdlib → terceiros → locais), sem imports não-usados.
- **Nomenclatura:** snake_case em Python, camelCase em TypeScript, PascalCase para classes/componentes.
- **Commits:** conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
- **Branch:** `main` é estável. Feature branches: `feat/<curta-descrição>`. PR para main com revisão.

## Estado atual do projeto

**Fase 0 — Concluída (passos 1–5).** O que está funcionando:

- Postgres 16 + Redis 7 via Docker Compose (`docker compose up -d`).
- Migration `0001` aplicável via `alembic upgrade head` — cria 6 tabelas: `users`, `cameras`, `persons`, `person_embeddings`, `alerts`, `audit_log`.
- API FastAPI com rotas:
  - `GET /health` — verifica Postgres + Redis, sem auth.
  - `POST /api/v1/auth/login` — JWT HS256, senha Argon2id, refresh token no Redis.
  - `POST /api/v1/auth/refresh` — rotação de refresh token.
  - `POST /api/v1/auth/logout` — revogação do refresh token.
- CLI: `python -m sinc.cli create-admin --email ... --username ... --password ...`
- 8 testes passando (`pytest tests/ -v`), com SQLite in-memory + httpx.AsyncClient.

**Pendente antes de avançar para Fase 1:**

- [ ] Validação manual do fluxo refresh/logout com Docker + Postgres real (Docker não estava ativo durante o desenvolvimento).
- [ ] ADR-009: decidir login por email vs. username após reunião com os operadores do Kan.
- [x] Endpoints de gerenciamento de usuários: `GET /api/v1/users` (MANAGER+), `POST /api/v1/users` (ADMIN), `PATCH /api/v1/users/{id}/deactivate` (ADMIN). 10 testes cobrindo RBAC e casos de erro.
- [ ] Passo 6: smoke test de YOLO + ArcFace em vídeo gravado de bancada — requer `scripts/download_models.sh` e GPU/CPU adequada.
- [ ] **Aguardando reunião com Kan** para destravar Fase 1 (especificações de servidor, lista de câmeras, watchlist real).

## Documentos de referência

- [`docs/arquitetura.docx`](docs/arquitetura.docx) — documento longo e formal (LGPD, contrato, fases, riscos). Útil como referência para decisões; não para uso diário.
- [`docs/implementacao.docx`](docs/implementacao.docx) — manual técnico enxuto com pseudocódigo e configurações. **Este é o que você deve consultar mais.**
- [`docs/decisoes.md`](docs/decisoes.md) — log das decisões importantes tomadas até agora, em markdown rastreável.
- [`docs/perguntas-pendentes.md`](docs/perguntas-pendentes.md) — o que ainda não sabemos sobre o ambiente do Kan.
