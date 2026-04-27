# SINC — Sistema Inteligente de Notificação e Captura

Projeto de visão computacional para o Supermercado Kan: reconhecimento facial restrito a uma watchlist, análise comportamental e Re-ID multi-câmera, com humano no laço para validação de todo alerta.

> **Para Claude Code e novos desenvolvedores:** comecem lendo [`CLAUDE.md`](CLAUDE.md). Ele tem os princípios não-negociáveis e a arquitetura em alto nível.

## Documentação

| Arquivo | Para quê |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Instruções persistentes para o Claude Code. Princípios, stack, convenções. |
| [`docs/arquitetura.docx`](docs/arquitetura.docx) | Documento formal completo (inclui LGPD, fases, contrato, riscos). Para referência. |
| [`docs/implementacao.docx`](docs/implementacao.docx) | Manual técnico com pseudocódigo, schemas, deploy. **Use no dia-a-dia.** |
| [`docs/decisoes.md`](docs/decisoes.md) | Log cronológico das decisões arquiteturais. |
| [`docs/perguntas-pendentes.md`](docs/perguntas-pendentes.md) | O que ainda não sabemos do ambiente do Kan. |

## Estado atual

Fase 0 — Preparação. Repositório sendo iniciado. Aguardando reunião com Kan para Fase 1.

## Roadmap (resumido)

- **Fase 0 (4–6 sem):** preparação, jurídico, servidor, watchlist inicial.
- **Fase 1 (6–10 sem):** MVP — Camada 1 em 2 câmeras de entrada.
- **Fase 2 (4–6 sem):** Tracking dirigido (Camada 3).
- **Fase 3 (8–16 sem):** Análise comportamental progressiva.
- **Fase 4 (12–24 sem):** Expansão para 300 câmeras.
- **Fase 5:** Operação contínua e melhoria.

Detalhes em `docs/arquitetura.docx`, Seção 10.

## Como começar (depois que o boilerplate existir)

```bash
# 1. Clonar e preparar
git clone <url-do-repo> sinc && cd sinc
cp .env.example .env  # editar valores

# 2. Baixar modelos (alguns GB)
./scripts/download_models.sh

# 3. Subir banco e Redis
docker compose up -d postgres redis

# 4. Migrations
docker compose run --rm api alembic upgrade head

# 5. Criar admin inicial
docker compose run --rm api python -m sinc.cli create-admin

# 6. Subir o resto
docker compose up -d

# 7. Validar
curl http://localhost:8000/api/health
```

## Licença

Privado. Uso interno.
