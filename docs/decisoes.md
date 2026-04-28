# Log de Decisões Arquiteturais — SINC

Formato leve baseado em ADR (Architecture Decision Records). Cada entrada registra: contexto, decisão, alternativas consideradas, consequências.

---

## ADR-001 — Arquitetura centralizada (não edge)

**Data:** 2026-04

**Contexto:** O plano original previa processamento distribuído em mini PCs próximos às câmeras (edge computing). Porém, o Supermercado Kan já dispõe de servidor central potente, e o número de câmeras (300) é compatível com processamento centralizado se houver GPU adequada.

**Decisão:** Arquitetura centralizada em servidor único do Kan, com 1 ou 2 GPUs NVIDIA dedicadas (RTX 4060+ para MVP, RTX 4090×2 ou equivalente para produção).

**Alternativas consideradas:**
- Edge com mini PCs N100 por grupo de câmeras (gRPC para servidor central).
- Cloud (descartada: latência, custo, LGPD).

**Consequências:**
- Stack mais simples; menos pontos de falha distribuídos.
- Dependência de uma máquina central — exige UPS, backup robusto, plano de recuperação.
- Arquitetura projetada para permitir migração futura para edge sem reescrita (componentes modulares + comunicação via Redis).

---

## ADR-002 — Filtro com watchlist + comportamento, não MCMOT populacional

**Data:** 2026-04

**Contexto:** O plano inicial mencionava MCMOT (Multi-Camera Multi-Object Tracking) como conceito principal. MCMOT populacional implicaria gerar embeddings de corpo para todas as pessoas em todas as câmeras, o que é juridicamente arriscado (LGPD) e tecnicamente caro.

**Decisão:** Sistema é um **filtro de atenção** com 3 camadas independentes:
- Camada 1 reconhece faces contra galeria fechada (~50 procurados).
- Camada 2 detecta comportamentos suspeitos via pose.
- Camada 3 (Re-ID) é ativada **somente** para indivíduos já flaggados.

Para clientes comuns, o sistema nunca gera embedding de corpo nem persiste qualquer dado.

**Alternativas consideradas:**
- MCMOT populacional (descartado por motivos legais e de proporcionalidade).
- Apenas Camada 1, sem comportamento (descartado por insuficiência: o Kan quer pegar furtos por ocultação).

**Consequências:**
- Defesa jurídica mais sólida (proporcionalidade evidente).
- Menos carga computacional.
- Re-ID dirigido tem limitação: se ninguém é flaggado, não há tracking. Aceitável.

---

## ADR-003 — Stack Python/FastAPI, não C++/gRPC

**Data:** 2026-04

**Contexto:** Pipeline de visão computacional pode ser implementado em C++ (mais rápido) ou Python (mais produtivo).

**Decisão:** Python 3.11 com FastAPI e asyncio. Otimização via ONNX Runtime / TensorRT em modelos críticos quando necessário.

**Justificativa:** Equipe pequena, ecossistema de IA fortemente Python, performance adequada com bibliotecas otimizadas (OpenCV, ONNX, PyTorch). C++ seria overengineering nesta escala.

**Consequências:** Maior produtividade, menos código boilerplate. Aceita-se que algumas inferências em CPU podem ser 20-30% mais lentas que C++ — mitigado por GPU.

---

## ADR-004 — Tracking com degradação graciosa explícita

**Data:** 2026-04

**Contexto:** Operadores podem demorar > 2 minutos para responder a um alerta. OSNet sozinho não mantém Re-ID confiável por tanto tempo (mudanças de iluminação, postura, oclusão).

**Decisão:** Tracking em camadas com **status explícito** mostrado ao operador:
- HIGH_CONFIDENCE (0–30s desde última detecção)
- MEDIUM (30s–3min)
- LOW (3–10min)
- LOST (>10min)

Cada transição é refletida no dashboard. O sistema nunca finge saber onde a pessoa está se não sabe.

**Alternativas consideradas:**
- Tracking com Kalman + Re-ID forte (impraticável em ambiente com 300 câmeras).
- Apenas alta-confiança curta (perde casos onde operador chega depois).

**Consequências:** Honestidade do sistema com o operador. Operador toma decisão informada sobre ir investigar ou marcar como perdido.

---

## ADR-005 — Persistência mínima

**Data:** 2026-04

**Contexto:** Câmeras processam milhares de pessoas por dia. Persistir tudo seria caro e juridicamente arriscado.

**Decisão:** Persistir apenas:
1. Eventos confirmados (verdadeiros e falso positivos rotulados).
2. Watchlist e seus embeddings.
3. Logs de auditoria.
4. Métricas operacionais agregadas (não pessoais).

Embeddings de não-match e frames de não-flaggados vivem em RAM por <1s e são descartados.

**Consequências:** Storage muito menor; menor exposição em caso de vazamento; alinhamento com princípio de minimização da LGPD.

---

## ADR-006 — Detectores comportamentais por regras explícitas (inicialmente)

**Data:** 2026-04

**Contexto:** Modelos supervisionados de detecção de furto exigem dataset rotulado que ainda não temos. Arquiteturas como ST-GCN são poderosas mas sem dados de treino são pouco úteis.

**Decisão:** Camada 2 inicia com **regras explícitas sobre keypoints** (RTMPose). Detectores: permanência anômala, pose de ocultação, manipulação de embalagem, movimento brusco. Conforme o Kan acumular vídeos rotulados de incidentes reais, classificadores supervisionados substituem ou complementam as regras.

**Consequências:**
- Auditável e debugável (regras são transparentes).
- Performance limitada — taxa de falso positivo será alta inicialmente.
- Operadores precisam ser preparados para isso.
- Fase 5 (manutenção) inclui retreino contínuo.

---

## ADR-007 — JWT com refresh, não sessões em banco

**Data:** 2026-04

**Decisão:** Auth via JWT (HS256), access token de 1h, refresh token de 7 dias com rotação a cada uso. Senhas com Argon2id. 2FA obrigatório para MANAGER e ADMIN.

**Justificativa:** Stateless, escalável, padrão da indústria para FastAPI.

---

## ADR-008 — PostgreSQL + Redis, não MongoDB

**Data:** 2026-04

**Decisão:** PostgreSQL 16 para persistência durável; Redis 7 para filas (Streams) e tracking ativo (Pub/Sub).

**Alternativas consideradas:** MongoDB (descartado: falta ACID forte, schema-less indesejado para audit_log, ecossistema SQL maduro).

---

## ADR-009 — Login por email (campo `username` do OAuth2) mantido por padrão

**Data:** 2026-04

**Contexto:** O formulário OAuth2PasswordRequestForm usa o campo `username`. Operadores de supermercado tendem a preferir email (menos chance de esquecer) a um username inventado. A implementação atual já aceita email no campo `username`.

**Decisão:** Manter login por email no campo `username` do formulário OAuth2. Nenhuma mudança no protocolo — só na semântica do campo.

**Alternativas consideradas:**
- Login por username puro (descartado: operadores esqueceriam o username, email é mais familiar).
- Aceitar ambos email e username (adiado: complexidade desnecessária agora).

**Consequências:** O campo `username` no formulário de login recebe um email. Pode confundir desenvolvedores novos — documentar no OpenAPI description do endpoint. Revisar com os operadores reais na reunião com o Kan antes de considerar mudança.

---

<!-- Adicionar novas decisões abaixo, mantendo o formato e a numeração -->
