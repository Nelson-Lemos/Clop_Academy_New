# CLOP Academy — Análise Completa do Projecto

> Documento de referência técnica e funcional do repositório **CLOP-Academy**.
> Actualizado em **26 de Outubro de 2026**, após a reconstrução da plataforma autenticada (shell, dashboards e módulos).
> Âmbito desta análise: portal institucional, autenticação, área do aluno, administração, API FastAPI, modelo de dados, segurança, estado de qualidade e próximos passos.
>
> **Estado resumido:** portal institucional, autenticação e plataforma autenticada (aluno e administração) reconstruídos com identidade preto/ouro; `tsc -b && vite build` e `oxlint` passam. A API FastAPI está implementada mas **não foi executada nesta sessão** (servidor local indisponível); a integração real está preparada, mas continua por validar em runtime.

---

## 1. Sumário executivo

O repositório contém dois produtos independentes que partilham o mesmo domínio de negócio:

| Componente | Tecnologia | Estado |
| --- | --- | --- |
| `Front/` | React 19 + TypeScript + Vite 8 | Portal institucional, autenticação e plataforma autenticada (aluno e administração) reconstruídos com identidade preto/ouro; build e lint passam |
| `backend/` | FastAPI + SQLAlchemy 2 + MySQL + Alembic | API LMS/institucional completa em código, com autenticação JWT, permissões, cursos, pagamentos, avaliações, certificados, mercados e auditoria |

O frontend deixou de ser uma página estática: passou a ter **routing por hash**, **formulário de login e registo ligado à API**, **intro cinematográfica** baseada no vídeo da marca e um **portal institucional re-tematizado** a partir do logótipo oficial.

O backend é substancialmente mais amplo do que aquilo que o frontend consome actualmente. Existe uma API pública (`/api/public/*`), uma área de aluno (`/api/aluno/*`) e uma área administrativa (`/api/admin/*`) com cerca de 80 endpoints. O frontend já consome autenticação, dashboard do aluno, inscrições, conteúdos, aulas, progresso, avaliações, pagamentos, certificados, notificações, perfil e os dois endpoints administrativos disponíveis (dashboard e cursos); o catálogo público do portal continua estático.

### Principais conclusões

1. **A identidade visual está consolidada.** O emblema, a paleta e o vídeo da marca foram extraídos dos activos oficiais e aplicados de forma consistente.
2. **O portal institucional foi preservado**, não substituído: a estrutura editorial existente foi mantida e re-tematizada.
3. **A autenticação está funcional ao nível do código**, mas depende de o backend e o MySQL estarem activos.
4. **O frontend ainda não consome o catálogo público.** O estado “catálogo em preparação” é estático, apesar de o seed do backend criar três cursos publicados.
5. **Não existem testes automatizados no repositório.** Existe apenas um script de diagnóstico (`backend/tools/smoke_test.py`), apontado para a porta `8001`.
6. **A camada de uploads está incompleta.** As pastas e configurações existem, mas não há endpoints `UploadFile` nem montagem de ficheiros estáticos.
7. **A integração de mercados é deliberadamente informativa.** Sem credenciais, nenhuma cotação é inventada — comportamento correcto e alinhado com o prompt mestre.

---

## 2. Objectivo e âmbito

O prompt mestre (preservado no Apêndice A) define a construção da plataforma digital oficial da **CLOP Academia Digital, LDA.**, instituição angolana de educação financeira, mercados, formação profissional, desenvolvimento pessoal, IA, transformação digital e empreendedorismo.

A fase actual priorizou:

- auditoria completa do repositório;
- reconstrução da identidade visual a partir dos activos oficiais;
- experiência animada no portal e na autenticação;
- ligação do login/registo à API existente;
- documentação técnica do estado do projecto.

O backend não foi reescrito nesta fase. A sua análise serve de base para as próximas fases (catálogo, área de aluno e administração no frontend).

---

## 3. Estrutura do repositório

```text
CLOP-Academy/
├─ agent.md                     # esta análise + prompt mestre original
├─ logo.jpg                     # logótipo oficial fornecido
├─ .gitignore
├─ Front/
│  ├─ index.html                # metadados, favicon, Open Graph
│  ├─ package.json              # scripts e dependências
│  ├─ vite.config.ts            # servidor exposto em 0.0.0.0
│  ├─ tsconfig*.json            # TypeScript strict
│  ├─ .env.example              # VITE_API_URL
│  ├─ README.md                 # documentação do frontend
│  ├─ public/brand/             # activos derivados da marca
│  └─ src/
│     ├─ main.tsx               # bootstrap React
│     ├─ App.tsx                # router por hash + shell autenticado
│     ├─ components/            # AppShell, PageHeader, StatCard, estados, BrandMark
│     ├─ config/institution.ts  # fonte única de contactos e assinatura
│     ├─ lib/api.ts             # cliente HTTP + sessão
│     ├─ lib/labels.ts          # tradução de estados, datas e valores
│     ├─ pages/AcademyHome.tsx  # portal institucional
│     ├─ pages/AuthScreen.tsx   # login/registo + intro
│     ├─ pages/aluno/           # dashboard, cursos, aulas, avaliações, certificados…
│     ├─ pages/admin/           # dashboard administrativo e gestão de cursos
│     └─ styles/                # brand.css, academy.css, auth.css, dashboard.css
└─ backend/
   ├─ app/
   │  ├─ main.py                # FastAPI, CORS, handlers, routers
   │  ├─ core/                  # config, database, security, instituição, utils
   │  ├─ dependencies/          # autenticação e permissões
   │  ├─ integrations/markets/  # adaptadores de fornecedores
   │  ├─ models/                # 31 tabelas SQLAlchemy
   │  ├─ routers/               # auth, public, student, admin_*
   │  ├─ schemas/               # contratos Pydantic
   │  └─ services/              # regras de negócio
   ├─ migrations/               # Alembic (revisão inicial)
   ├─ tools/smoke_test.py       # diagnóstico ponta a ponta
   ├─ uploads/                  # comprovativos (não servidos publicamente)
   ├─ alembic.ini
   ├─ requirements.txt
   ├─ seed.py
   └─ .env.example
```

O projecto é um repositório Git com remoto em `github.com/Nelson-Lemos/Clop_Academy_New` (branch `main`), e a Vercel compila a partir desse remoto com raiz de projecto em `Front`. O `.gitignore` está preparado para Python, Node, ambientes virtuais, builds, uploads e segredos.

---

## 4. Frontend

### 4.1 Stack e ferramentas

| Item | Versão / escolha |
| --- | --- |
| React / React DOM | 19.2.8 |
| TypeScript | 6.0.2, modo `strict` com `noUnusedLocals` e `noUnusedParameters` |
| Vite | 8.3.0, plugin React 6.1.1 |
| Ícones | `lucide-react` 1.47.0 |
| Lint | `oxlint` 1.81.0 |
| Routing | Router próprio por `window.location.hash` (sem `react-router`) |
| Estado | `useState`/`useEffect` locais; sem Redux/Zustand |
| Estilos | CSS puro com variáveis, três folhas globais |

Scripts:

```powershell
npm.cmd run dev       # servidor Vite em 0.0.0.0:5173
npm.cmd run build     # tsc -b && vite build
npm.cmd run lint      # oxlint
npm.cmd run preview   # pré-visualização em 0.0.0.0:4173
```

> Em Windows/PowerShell deste ambiente, o shim `npm` está bloqueado; usar `npm.cmd`.

Não foram adicionadas dependências novas para a reconstrução visual nem para o routing.

### 4.2 Arranque e routing

`src/main.tsx` monta `<App />` em `StrictMode`. `src/App.tsx` implementa um router mínimo:

| Hash | Ecrã | Título do documento |
| --- | --- | --- |
| `#/entrar` | `AuthScreen` modo `login` | `Entrar — CLOP Academia Digital` |
| `#/registar` | `AuthScreen` modo `register` | `Criar conta — CLOP Academia Digital` |
| Qualquer outro valor | `AcademyHome` | `CLOP Academia Digital — Educação Financeira & Mercados` |

Comportamentos relevantes:

- O router ouve `hashchange`; não recarrega a página.
- Ao voltar à home, um hash de âncora (`#sobre`, `#formacao`, etc.) é respeitado e a secção é trazida para a vista no frame seguinte.
- O portal usa âncoras internas para navegação; a autenticação usa rotas `#/...`.
- Não há 404 dedicado: qualquer rota desconhecida cai na home.
- O título é actualizado por efeito, não por metadados server-side.

### 4.3 Identidade visual

#### Proveniência

A identidade foi derivada dos activos oficiais da marca; o vídeo está incorporado no frontend em `Front/public/brand/clop-brand-film.mp4`:

- emblema com touro, escudo, coroa/crest e torres;
- fundo preto e dourado;
- tipografia serifada de inspiração clássica para a marca;
- texto oficial: `CLOP`, `ACADEMIA DIGITAL, LDA`, `CONSULTORIA & INVESTIMENTOS`, `ANÁLISE | ESTRATÉGIA | RESULTADOS`, `CONFIANÇA . DISCIPLINA . LUCRO`;
- paleta dourada (`#f4cc48`), bronze (`#90752d` / `#8a6a23`) e azeitona (`#9aaa47`).

#### Activos em `Front/public/brand/`

| Ficheiro | Formato / dimensão | Uso |
| --- | --- | --- |
| `clop-logo.jpg` | 640×640 | Logótipo original preservado |
| `clop-lockup.png` | 640×640, fundo transparente | Assinatura completa |
| `clop-emblem.png` | 428×437, fundo transparente | Favicon, cabeçalho, marca de água |
| `clop-brand-film.mp4` | 478×850, ~8 s, H.264/AAC | Intro, fundo de autenticação e hero |
| `clop-brand-poster.jpg` | 478×850 | Poster dos vídeos |
| `clop-og.jpg` | 1200×630 | Open Graph / Twitter Card |

O vídeo tem áudio, mas é sempre reproduzido com `muted` para permitir autoplay nos navegadores.

#### Design tokens (`src/styles/brand.css`)

| Token | Valor | Papel |
| --- | --- | --- |
| `--clop-black` | `#050505` | Fundo principal |
| `--clop-black-soft` | `#0b0a08` | Fundo secundário |
| `--clop-black-lift` | `#12100b` | Superfícies elevadas |
| `--clop-ink` | `#171208` | Texto sobre creme |
| `--clop-gold` | `#c9a227` | Ouro institucional |
| `--clop-gold-bright` | `#f4cc48` | Destaques e CTAs |
| `--clop-gold-pale` | `#f6e7b8` | Texto dourado suave |
| `--clop-bronze` | `#8a6a23` | Detalhes e subtítulos |
| `--clop-olive` | `#9aaa47` | Acento secundário |
| `--clop-cream` | `#f7f2e6` | Fundo claro / texto sobre preto |
| `--clop-cream-deep` | `#efe5d0` | Faixas claras |
| `--clop-muted` | `#7a7364` | Texto secundário |
| `--clop-line` | `rgba(201,162,39,.24)` | Linhas douradas |
| `--clop-line-soft` | `rgba(247,242,230,.12)` | Divisores |
| `--font-display` | Palatino/Book Antiqua/Georgia | Títulos |
| `--font-ui` | Inter/Segoe UI/Arial | Interface |
| `--ease-out` | `cubic-bezier(.22,.78,.16,1)` | Movimento principal |
| `--ease-soft` | `cubic-bezier(.4,0,.2,1)` | Movimento suave |

Movimento partilhado: `clop-fade-up`, `clop-fade`, `clop-line-in`, `clop-spin`, `clop-spin-reverse`, `clop-glow`, `clop-shimmer`, `clop-marquee`, `clop-float`, `clop-progress`. Todos são neutralizados por `prefers-reduced-motion: reduce`.

#### Componente `BrandMark`

`BrandMark` é a assinatura reutilizável: emblema + `CLOP` + `Academia Digital`. Aceita:

- `theme`: `light` (texto creme) ou `dark` (texto tinta);
- `href`: destino, por omissão `#inicio`;
- `emblemSize`: tamanho do emblema;
- `className`.

O emblema tem `alt=""` porque o link já possui `aria-label`; evita-se duplicação para leitores de ecrã.

### 4.4 Portal institucional (`AcademyHome.tsx`)

O portal mantém a estrutura editorial anterior, agora com bandas alternadas creme/preto, cabeçalho fixo com desfoque e uma composição hero cinematográfica.

| Secção | Âncora | Conteúdo |
| --- | --- | --- |
| Cabeçalho | — | Marca, navegação, `Entrar`, `Criar conta`; menu móvel acessível |
| Hero | `#inicio` | Título, assinatura, CTAs, pilares, vídeo da marca em moldura vertical, emblema em marca de água, órbitas e etiquetas |
| Credo | — | Marquee dourado com Análise · Estratégia · Resultados · Confiança · Disciplina · Lucro |
| Quem somos | `#sobre` | Missão, visão e valores em três cartões numerados |
| Áreas de actuação | `#areas` | Seis áreas com ícones |
| Formação | `#formacao` | Estado vazio explícito + CTA de conta + pedido de informações por e-mail |
| Mercados | `#mercados` | Explicação responsável + estado “Dados de mercado indisponíveis” |
| Actualidade | `#actualidade` | Estados vazios para publicações e eventos |
| Iniciativas | `#iniciativas` | Seis linhas de trabalho marcadas como “Planeada” |
| Parcerias | `#parcerias` | Formulário que abre o cliente de e-mail |
| Newsletter | `#actualizacoes` | Formulário com consentimento que abre o cliente de e-mail |
| Rodapé | `#contactos` | Marca, assinatura, navegação, contactos, credo |
| Legal | `#privacidade`, `#termos` | Avisos no rodapé (não são páginas autónomas) |

Comportamentos e limites:

- **Nenhum dado é inventado.** Cursos, artigos, eventos e mercados aparecem como indisponíveis.
- **Formulários de parceria e newsletter não submetem para a API.** Validam no navegador e preparam um `mailto:`; o portal não armazena esses dados.
- **A página não consome `/api/public/*`.** O conteúdo é estático e mantido em `AcademyHome.tsx`/`institution.ts`.
- O estado vazio do catálogo **não reflecte o seed do backend**, que cria três cursos publicados. É uma incoerência temporária até à ligação do catálogo.
- As ligações `#privacidade` e `#termos` apontam para blocos do rodapé, não para páginas legais completas.
- A navegação móvel usa um botão com `aria-expanded`, `aria-controls` e fecha ao seleccionar uma ligação.
- O e-mail de contacto e os telefones vêm de `institution.ts`; não estão duplicados na página.

### 4.5 Autenticação (`AuthScreen.tsx`)

O ecrã de autenticação é dividido em duas zonas:

1. **Palco esquerdo** — vídeo da marca em loop ambiente, véu escuro, grão, marca, descritor, credo e pilares.
2. **Painel direito** — formulário, estados de sessão, erros e informação legal.

#### Intro cinematográfica

- Mostrada apenas uma vez por sessão, controlada por `sessionStorage` (`clop:intro-seen`).
- O vídeo começa em `3.1 s`, fica `muted`, `playsInline` e termina com `onEnded`.
- Fecho automático após **5,2 s**, botão “Saltar introdução” e tecla `Escape`.
- Transição de saída de 900 ms (`is-leaving`), com barra de progresso.
- Se `sessionStorage` estiver indisponível, a intro volta na sessão seguinte — falha segura.
- O palco ambiente procura `4.25 s` e mantém o loop entre `4.25 s` e `7.82 s`.

#### Login

Campos: e-mail e palavra-passe, com mostrar/ocultar, aviso de Caps Lock, “manter sessão neste dispositivo” e recuperação por e-mail de apoio. Submete para `POST /auth/login`.

#### Registo

Campos: nome completo, e-mail, telefone opcional, província opcional, palavra-passe, confirmação e aceitação de termos. Inclui:

- medidor de força em cinco níveis;
- regras visíveis: mínimo 8 caracteres, uma letra e um número;
- confirmação em tempo real;
- aviso de Caps Lock;
- botão desactivado enquanto as regras obrigatórias não estiverem cumpridas.

O frontend envia `aceite_termos: true` e `aceite_privacidade: true` quando o utilizador aceita. O backend valida explicitamente `aceite_termos`; o campo `aceite_privacidade` existe no schema, mas não é verificado na rota.

#### Sessão

- Ao abrir, se existir token, chama `GET /auth/me`.
- Se a API responder `401`, limpa a sessão.
- Se a API estiver indisponível, mostra um aviso e mantém os dados em cache.
- Com sessão válida, apresenta nome, e-mail, perfil, província e estado, com opção de terminar sessão.
- “Terminar sessão” é local: remove tokens e cache, sem endpoint de logout no backend.
- O perfil de role é traduzido (`STUDENT` → Aluno, etc.).

#### Armazenamento de tokens

| Chave | Conteúdo |
| --- | --- |
| `clop:access` | JWT de acesso |
| `clop:refresh` | JWT de renovação |
| `clop:user` | Cache do utilizador |

Com “manter sessão”, usa `localStorage`; sem essa opção, `sessionStorage`. O refresh é automático quando `/auth/me` devolve `401`.

### 4.6 Responsividade, acessibilidade e SEO

- Layout fluido com `clamp()`, grelhas que colapsam e menu móvel.
- Foco visível, etiquetas em todos os campos, `aria-live` para erros e estados, `role="alert"`, `aria-expanded`, `aria-controls`, `aria-selected`.
- Texto alternativo: emblemas decorativos com `alt=""`; o link tem rótulo.
- `prefers-reduced-motion` desactiva animações e scroll suave.
- `index.html` define `lang="pt-AO"`, descrição, `theme-color`, favicon, Apple Touch Icon, Open Graph e Twitter Card.
- O `og:image` é relativo (`/brand/clop-og.jpg`); em produção deve ser absolute para pré-visualizações sociais.
- Não existem `robots.txt`, `sitemap.xml`, canónicos nem dados estruturados.
- As áreas privadas não são indexáveis por ausência de páginas estáticas, mas não há `noindex` explícito.

### 4.7 Integração com a API

`src/lib/api.ts` centraliza o acesso:

```text
VITE_API_URL (por omissão: http://localhost:8000/api)
```

| Função | Método e rota | Efeito |
| --- | --- | --- |
| `authApi.login` | `POST /auth/login` | Guarda tokens e utilizador |
| `authApi.register` | `POST /auth/registo` | Guarda tokens e utilizador |
| `authApi.me` | `GET /auth/me` | Valida sessão; tenta refresh em `401` |
| `refreshAccessToken` | `POST /auth/refresh` | Renova tokens |
| `authApi.logout` | — | Limpa armazenamento local |

Contrato de autenticação:

```json
{
  "access_token": "…",
  "refresh_token": "…",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nome_completo": "…",
    "email": "…",
    "telefone": null,
    "role": "STUDENT",
    "estado": "ACTIVE",
    "aceite_termos_em": "…",
    "email_verificado_em": null,
    "criado_em": "…",
    "perfil_aluno": { "…": "…" },
    "permissoes": []
  }
}
```

Tratamento de erros:

- `ApiError` transporta `status` e lista de `details`.
- Erros de rede produzem uma mensagem compreensível em português.
- Erros `422` do FastAPI são normalizados (`detail` string ou lista de `msg`).
- O frontend não expõe stack traces nem detalhes internos.

O cliente está preparado para renovação de token, mas a renovação só é exercitada em `/auth/me`; chamadas futuras devem reutilizar o mesmo padrão.

### 4.8 Plataforma autenticada — shell e módulos

A área reservada deixou de ser um conjunto de páginas isoladas e passou a ter uma **estrutura de aplicação** consistente.

**Shell (`components/AppShell.tsx`)**

- Navegação lateral persistente com identidade CLOP (preto, ouro, creme), agrupada por contexto: *Aprendizagem* (aluno) ou *Gestão* (administração).
- Itens de aluno: Visão geral, Meus cursos, Avaliações, Certificados, Pagamentos, Notificações e Perfil.
- Itens de gestão: Painel de gestão e Gestão de cursos, mostrados conforme o `role` (`ADMIN`, `SUPERADMIN`, `EDITOR`, `FINANCE`, `INSTRUCTOR`).
- Barra superior com breadcrumb, atalho para o site institucional, notificações (aluno) e identificação do utilizador.
- Gaveta móvel com *scrim*, fecho por `Escape` e fecho automático na mudança de rota.
- Rodapé institucional e ligação “Voltar ao site”.

**Sistema visual (`styles/dashboard.css`)**

- Paleta própria da aplicação (`--app-*`) assente nos tokens da marca (`--clop-*`), com superfícies creme, cartões claros e acentos ouro.
- Componentes reutilizáveis: `.app-card`, `.stat-card`, `.badge`, `.progress`, `.app-table`, `.toolbar`, `.filter-chip`, `.empty-state`, `.error-state`, `.skeleton`.
- Tipografia: serifa da marca nos títulos, sans-serif na interface.
- Estados de foco visíveis, *skeletons* de carregamento, estados vazios com acção e mensagens de erro com nova tentativa.
- Responsividade em 1180 px (grelhas a uma coluna), 1024 px (sidebar off-canvas), 720 px e 520 px.
- Respeito por `prefers-reduced-motion`.

**Módulos do aluno**

| Rota | Ecrã | Conteúdo principal |
| --- | --- | --- |
| `#/dashboard` | Visão geral | Hero de retoma com anel de progresso, 4 KPIs, cartões de curso, próximas aulas e notificações recentes |
| `#/inscricoes` | Meus cursos | Filtros por estado, pesquisa, tabela com progresso e acções |
| `#/cursos/:id` | Sala de aula | Currículo em módulos expansíveis, resumo lateral com progresso e CTA para a próxima aula |
| `#/aulas/:courseId/:lessonId` | Aula | Vídeo/conteúdo, materiais, estado e marcação de conclusão |
| `#/avaliacoes` | Avaliações | Cartões com estado, tentativas, nota mínima e última nota |
| `#/avaliacoes/:id` | Avaliação | Perguntas numeradas, progresso de respostas, submissão e ecrã de resultado |
| `#/pagamentos` | Pagamentos | Resumo de valores e tabela de referências |
| `#/certificados` | Certificados | Cartões com selo, código, nota e data de emissão |
| `#/notificacoes` | Notificações | Filtro “todas / não lidas”, marcação individual e global |
| `#/perfil` | Perfil | Hero de conta, dados pessoais, perfil de aluno, objectivo/biografia e estado da conta |

**Módulos de administração**

| Rota | Ecrã | Conteúdo principal |
| --- | --- | --- |
| `#/admin/dashboard` | Painel de gestão | 6 KPIs, gráfico de barras de inscrições por curso, resumo operacional e acções rápidas |
| `#/admin/cursos` | Gestão de cursos | Filtros por estado de publicação, pesquisa e tabela do catálogo |

**Componentes transversais**

- `PageHeader` — eyebrow, título, descrição e acções.
- `StatCard` — KPI com ícone, valor, contexto e tom.
- `EmptyState` / `ErrorState` / `LoadingState` / `DashboardSkeleton`.
- `lib/labels.ts` — tradução de estados, funções, datas, moeda (AOA) e iniciais.

**Notas de implementação**

- Não foram adicionadas dependências: os ícones usam `lucide-react`, já presente.
- O perfil é apenas de leitura porque o cliente não expõe endpoint de actualização de perfil.
- A submissão de avaliação volta a pedir o detalhe após o `POST`, para apresentar a nota corrigida pelo servidor.
- Os dados continuam a vir exclusivamente da API; não foram introduzidos valores fictícios.

---

## 5. Backend

### 5.1 Stack

| Item | Escolha |
| --- | --- |
| Framework | FastAPI |
| ORM | SQLAlchemy 2 (`Mapped`, `mapped_column`) |
| Base de dados | MySQL via `pymysql` (predefinição `clop_academy`) |
| Migrações | Alembic (revisão inicial `fc970855c30f`) |
| Validação | Pydantic v2 / pydantic-settings |
| Autenticação | JWT HS256 (`python-jose`) + `bcrypt` |
| PDF | `reportlab` |
| HTTP cliente | `httpx` |
| Testes | `pytest` declarado, sem suíte criada |

### 5.2 Arranque

`app/main.py`:

- cria a aplicação com título, descrição e versão de `settings`;
- monta CORS restritivo com origens explícitas;
- registra os routers sob `settings.API_PREFIX` (`/api`);
- em startup, publica artigos agendados cuja hora já passou;
- normaliza erros HTTP, validação (`422`) e excepções não tratadas (`500`);
- expõe `GET /` e `GET /api/health`;
- disponibiliza `/docs`, `/redoc` e `/openapi.json`;
- cria `UPLOAD_DIR` e `uploads/comprovativos`, embora ainda não sirva ficheiros nem aceite uploads por endpoint.

### 5.3 Configuração

Fonte: `backend/app/core/config.py` e `backend/.env.example`.

| Variável | Predefinição | Notas |
| --- | --- | --- |
| `PROJECT_NAME` | `CLOP Academy` | Metadados |
| `ENVIRONMENT` | `development` | `production` reduz logs |
| `DEBUG` | `false` | — |
| `API_PREFIX` | `/api` | **Não** é `/api/v1` |
| `DATABASE_URL` | `mysql+pymysql://root@localhost:3306/clop_academy` | MySQL local |
| `SECRET_KEY` | valor inseguro de exemplo | **Obrigatório trocar** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT de acesso |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | JWT de renovação |
| `LOGIN_MAX_ATTEMPTS` | `5` | Por chave IP+e-mail |
| `LOGIN_LOCK_MINUTES` | `15` | Janela do limitador |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Lista separada por vírgulas |
| `PUBLIC_SITE_URL` | `http://localhost:5173` | Links públicos |
| `UPLOAD_DIR` | `uploads` | Criado no arranque |
| `MAX_UPLOAD_MB` | `10` | Ainda sem endpoint de upload |
| `SEED_ADMIN_EMAIL` | `admin@clop.academy` | Primeiro administrador |
| `SEED_ADMIN_PASSWORD` | `TroqueEstaPassword_2026!` | **Trocar antes de produção** |
| `SEED_ADMIN_NAME` | `Administrador CLOP` | — |
| `INSTITUTION_*` | dados oficiais | Identidade institucional |
| `INSTITUTION_SOCIAL_LINKS` | vazio | Redes não configuradas não aparecem |
| `MARKET_*` | vazio | Sem chaves, estado informativo |
| `MARKET_CACHE_TTL_SECONDS` | `300` | Cache em memória |
| `MARKET_REQUEST_TIMEOUT_SECONDS` | `10` | Timeout dos fornecedores |

### 5.4 Autenticação, sessão e segurança

- **Hash:** bcrypt com salt por palavra-passe.
- **JWT:** HS256; `sub` é o ID do utilizador; claims `typ` (`access`/`refresh`) e `exp`.
- **Duração:** acesso 30 minutos; refresh 7 dias.
- **Validação:** cada pedido protegido descodifica o token, exige `typ=access` e confirma que o utilizador existe e está `ACTIVE`.
- **Registo:** e-mail normalizado para minúsculas; duplicados devolvem `409`; palavra-passe com mínimo 8 caracteres, letra e número; `aceite_termos` obrigatório.
- **Login:** mensagem genérica para credenciais inválidas; auditoria de sucesso e falha; atualização de `ultimo_acesso_em`.
- **Limitador:** 5 falhas por `IP:e-mail` numa janela de 15 minutos, **em memória**, adequado apenas a uma instância.
- **Permissões:** sempre verificadas no backend por `require_permissions`, `require_roles`, `require_admin`, `require_superadmin` ou `require_staff`.
- **CORS:** origens explícitas, credenciais permitidas, métodos e cabeçalhos limitados.
- **SQL injection:** mitigada pelo ORM e queries parametrizadas.
- **XSS:** o frontend React escapa conteúdo; não há HTML cru injetado.
- **Tokens no browser:** `localStorage`/`sessionStorage` são práticos, mas expostos a XSS. Para produção, considerar cookies `HttpOnly`/`Secure`/`SameSite` ou reforçar CSP.
- **Auditoria:** operações sensíveis são registadas em `audit_logs`.
- **Logs:** não registam palavras-passe nem tokens.

### 5.5 Modelo de dados

31 tabelas, agrupadas por domínio:

| Domínio | Tabelas |
| --- | --- |
| Identidade e acesso | `users`, `student_profiles`, `instructor_profiles` |
| Catálogo e aprendizagem | `courses`, `course_modules`, `lessons`, `lesson_materials`, `cohorts`, `enrollments`, `progress_records` |
| Avaliação e certificação | `assessments`, `questions`, `submissions`, `certificates` |
| Financeiro | `payments`, `payment_receipts` |
| Editorial | `categories`, `articles`, `events`, `event_registrations`, `campaigns`, `advertisements`, `projects` |
| Mercados | `market_quotes`, `market_instruments`, `economic_events`, `macro_indicators` |
| Comunicação e auditoria | `notifications`, `contact_messages`, `newsletter_subscriptions`, `audit_logs` |

Relações e integridade relevantes:

- `enrollments` tem restrição única `(user_id, course_id)`, prevenindo inscrições duplicadas.
- Eliminações em cascata para perfis, inscrições, progresso, certificados e notificações.
- `progress_records` liga inscrição e aula, com percentagem e última posição.
- `payments` e `payment_receipts` separam pagamento de comprovativo.
- `certificates` tem código público verificável.
- `market_quotes` guarda fonte, frescura, data de mercado e momento de consulta.
- `audit_logs` registra actor, acção, entidade e detalhe.

Estados principais:

- Utilizador: `ACTIVE`, `INACTIVE`, `SUSPENDED`.
- Funções: `STUDENT`, `INSTRUCTOR`, `EDITOR`, `FINANCE`, `ADMIN`, `SUPERADMIN`.
- Curso: publicado/rascunho/arquivado; modalidade online/presencial/híbrido.
- Inscrição: pendente, confirmada, cancelada, concluída (conforme `EnrollmentStatus`).
- Pagamento: pendente, confirmado, recusado, reembolsado.
- Artigo: rascunho, agendado, publicado, arquivado.
- Evento: planeado, publicado, cancelado, concluído.
- Certificado: emitido, revogado, etc.
- Frescura de mercado: tempo real, atrasado, histórico, indisponível.

### 5.6 Routers e endpoints

Prefixo global: `/api`.

#### Autenticação (`/api/auth`)

| Método | Rota | Acesso | Descrição |
| --- | --- | --- | --- |
| POST | `/registo` | Público | Cria aluno e devolve tokens (`201`) |
| POST | `/login` | Público | Autentica e devolve tokens |
| POST | `/refresh` | Público | Renova tokens com refresh válido |
| GET | `/me` | Autenticado | Utilizador, perfil e permissões |
| PUT | `/perfil` | Autenticado | Actualiza nome, telefone e perfil de aluno |
| POST | `/password` | Autenticado | Altera palavra-passe com verificação da actual |

#### Portal público (`/api/public`)

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/instituicao` | Identidade, contactos, missão, visão, valores |
| GET | `/home` | Agregado de cursos, artigos, eventos, campanhas, projectos e mercados |
| GET | `/cursos` | Catálogo paginado com pesquisa e filtros (`q`, `area`, `modalidade`, `nivel`, `somente_abertos`) |
| GET | `/cursos/{slug}` | Detalhe de curso publicado |
| GET | `/artigos` | Artigos publicados, com filtros e paginação |
| GET | `/artigos/{slug}` | Detalhe de artigo |
| GET | `/categorias` | Categorias editoriais |
| GET | `/eventos` | Eventos publicados |
| GET | `/eventos/{slug}` | Detalhe de evento |
| POST | `/eventos/{id}/inscricao` | Inscrição em evento |
| GET | `/projectos` | Projectos e iniciativas |
| GET | `/campanhas` | Campanhas activas |
| POST | `/campanhas/{id}/clique` | Registo de clique |
| POST | `/contactos` | Mensagem institucional |
| POST | `/newsletter` | Subscrição com consentimento |
| GET | `/mercados` | Visão de mercados com fonte e frescura |
| GET | `/mercados/fontes` | Estado das integrações |
| GET | `/certificados/{codigo}` | Verificação pública de certificado |

#### Área do aluno (`/api/aluno`)

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/dashboard` | Métricas, próximas aulas, avaliações e notificações |
| GET | `/inscricoes` | Inscrições do próprio aluno |
| POST | `/inscricoes` | Nova inscrição com aceitação de termos |
| POST | `/inscricoes/{id}/cancelar` | Cancelamento |
| POST | `/inscricoes/{id}/estado` | Alteração de estado (quando autorizada) |
| GET | `/cursos/{id}/conteudo` | Módulos e aulas, sujeitos a acesso |
| GET | `/cursos/{id}/aulas/{lesson_id}` | Detalhe da aula |
| POST | `/cursos/{id}/progresso` | Marca aula concluída e recalcula progresso |
| GET | `/avaliacoes` | Avaliações disponíveis |
| GET | `/avaliacoes/{id}` | Perguntas sem resposta correcta exposta |
| POST | `/avaliacoes/submissao` | Submissão e correcção no backend |
| GET | `/avaliacoes/{id}/historico` | Histórico de tentativas |
| GET | `/pagamentos` | Pagamentos do aluno |
| GET | `/certificados` | Certificados emitidos |
| POST | `/certificados/{inscricao_id}/emitir` | Emissão após verificação de requisitos |
| GET | `/notificacoes` | Notificações |
| POST | `/notificacoes/{id}/ler` | Marca uma como lida |
| POST | `/notificacoes/ler-todas` | Marca todas como lidas |

#### Administração — cursos (`/api/admin`)

Dashboard, CRUD de cursos, módulos, aulas, materiais e turmas; listagem e alteração de estado de inscrições.

| Método | Rota | Permissão |
| --- | --- | --- |
| GET | `/dashboard` | `relatorios:ver` |
| GET | `/cursos` | `cursos:ver` |
| GET | `/cursos/{id}` | `cursos:ver` |
| POST/PUT | `/cursos`, `/cursos/{id}` | `cursos:gerir` |
| POST | `/cursos/{id}/estado` | `cursos:gerir` |
| DELETE | `/cursos/{id}` | `cursos:gerir` |
| POST/PUT/DELETE | `/cursos/{id}/modulos`, `/modulos/{id}` | `cursos:gerir` |
| POST/PUT/DELETE | `/modulos/{id}/aulas`, `/aulas/{id}` | `cursos:gerir` |
| POST/DELETE | `/aulas/{id}/materiais`, `/materiais/{id}` | `cursos:gerir` |
| POST | `/cursos/{id}/turmas` | `cursos:gerir` |
| GET | `/inscricoes` | `inscricoes:ver` |
| POST | `/inscricoes/{id}/estado` | `inscricoes:gerir` |

#### Administração — editorial e eventos (`/api/admin`)

Categorias, artigos, eventos, campanhas, anúncios e projectos.

- Categorias e artigos: `editorial:gerir`.
- Eventos e inscrições em eventos: `eventos:gerir`.
- Campanhas e anúncios: `campanhas:gerir`.
- Projectos: `editorial:gerir`.

#### Administração — operações (`/api/admin`)

| Área | Endpoints | Permissão |
| --- | --- | --- |
| Utilizadores | `GET/POST /utilizadores`, `PATCH /utilizadores/{id}/estado` | `utilizadores:gerir` |
| Alteração de função | `PATCH /utilizadores/{id}/funcao` | `SUPERADMIN` |
| Pagamentos | `GET /pagamentos`, `POST /pagamentos/{id}/confirmar` | `pagamentos:ver` / `pagamentos:gerir` |
| Submissões | `GET /avaliacoes/submissoes` | `pagamentos:ver` |
| Contactos | `GET /contactos`, `PATCH /contactos/{id}` | `pagamentos:ver` |
| Auditoria | `GET /auditoria` | `auditoria:ver` |
| Mercados | fontes, sincronização, cotações, instrumentos, indicadores, calendário | `mercados:gerir` |
| Relatórios | `GET /relatorios/inscricoes` | `pagamentos:ver` |

### 5.7 Matriz de permissões

| Permissão | STUDENT | INSTRUCTOR | EDITOR | FINANCE | ADMIN | SUPERADMIN |
| --- | --- | --- | --- | --- | --- | --- |
| `cursos:ver` | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| `cursos:gerir` | — | — | — | — | ✓ | ✓ |
| `turmas:gerir` | — | ✓ | — | — | ✓ | ✓ |
| `alunos:ver` | — | ✓ | — | ✓ | ✓ | ✓ |
| `alunos:gerir` | — | — | — | — | ✓ | ✓ |
| `inscricoes:ver` | — | — | — | ✓ | ✓ | ✓ |
| `inscricoes:gerir` | — | — | — | ✓ | ✓ | ✓ |
| `pagamentos:ver` | — | — | — | ✓ | ✓ | ✓ |
| `pagamentos:gerir` | — | — | — | ✓ | ✓ | ✓ |
| `editorial:gerir` | — | — | ✓ | — | ✓ | ✓ |
| `eventos:gerir` | — | — | ✓ | — | ✓ | ✓ |
| `campanhas:gerir` | — | — | ✓ | — | ✓ | ✓ |
| `mercados:gerir` | — | — | — | — | ✓ | ✓ |
| `utilizadores:gerir` | — | — | — | — | — | ✓ |
| `auditoria:ver` | — | — | — | — | — | ✓ |
| `relatorios:ver` | — | — | ✓ | ✓ | ✓ | ✓ |
| `avaliacoes:corrigir` | — | ✓ | — | — | ✓ | ✓ |

O `ADMIN` tem todas as permissões **excepto** `utilizadores:gerir` e `auditoria:ver`, reservadas ao `SUPERADMIN`.

### 5.8 Serviços

| Serviço | Responsabilidade |
| --- | --- |
| `auth_service` | Autenticar, procurar por e-mail e criar aluno com perfil |
| `course_service` | Serialização e regras de catálogo |
| `enrollment_service` | Inscrição, estados, acesso e progresso |
| `assessment_service` | Avaliações, submissões e classificação |
| `certificate_service` | Emissão e verificação de certificados |
| `content_service` | Artigos, publicação agendada, eventos e editorial |
| `dashboard_service` | Métricas administrativas e de aluno |
| `market_service` | Cache, sincronização, fontes e visão de mercado |
| `notification_service` | Criação e leitura de notificações |
| `audit_service` | Registo de auditoria |

As regras críticas (pagamento, acesso a conteúdo, correcção, certificado) residem no backend. O frontend nunca é autoridade.

### 5.9 Seed

`backend/seed.py` é idempotente e corre com `python seed.py` ou `python seed.py --sem-demo`.

| Conteúdo | Detalhe |
| --- | --- |
| Administrador | `admin@clop.academy` / `TroqueEstaPassword_2026!`, `SUPERADMIN` |
| Formador demo | `formacao@clop.academy` / `Formacao_Clop_2026!`, `INSTRUCTOR` |
| Categorias | 6 (mercados, educação financeira, IA, empreendedorismo, carreira, notícias) |
| Cursos | 3 publicados: Literacia Financeira, Leitura de Mercados, IA Aplicada ao Negócio |
| Estrutura | Módulos, aulas, materiais, avaliação com perguntas e turma |
| Artigos | 3 publicados (conteúdo de demonstração identificado) |
| Eventos | 2 publicados (sessão presencial e webinar) |
| Projectos | 3 (em curso e planeado) |
| Campanha | “Inscrições abertas — Formação 2026” em destaque na home |

Observações:

- O seed **não** cria alunos, inscrições, pagamentos nem certificados.
- Os textos de demonstração contêm imperfeições herdadas (por exemplo, palavras em inglês no meio de frases portuguesas). Devem ser revistos antes de publicação.
- O seed é adequado a desenvolvimento; não deve ser executado em produção sem revisão de conteúdo e credenciais.

### 5.10 Migrações e execução

- Alembic configurado em `backend/alembic.ini` e `backend/migrations/`.
- Existe uma revisão inicial aplicada: `fc970855c30f_initial_schema.py`.
- Há um `.pyc` de uma revisão antiga (`c35b548fafb3`) em `__pycache__`, sem fonte correspondente; é resíduo e deve ser ignorado/limpo.
- Comandos típicos (a partir de `backend/`, com o ambiente virtual activo):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

Pré-requisitos: MySQL activo e base `clop_academy` criada; `SECRET_KEY` e credenciais revistas; CORS coerente com a origem do frontend.

---

## 6. Fluxos ponta a ponta

### 6.1 Registo de aluno

1. Visitante abre `#/registar`.
2. Preenche nome, e-mail, telefone/província opcionais, palavra-passe e confirmação.
3. Aceita termos e privacidade.
4. Frontend valida e envia `POST /api/auth/registo`.
5. Backend normaliza o e-mail, valida a palavra-passe, verifica duplicados e cria `User` + `StudentProfile`.
6. Devolve `201` com tokens e utilizador.
7. Frontend guarda a sessão e mostra o estado autenticado.
8. Auditoria regista o registo.

### 6.2 Login

1. Visitante abre `#/entrar`.
2. Envia e-mail e palavra-passe.
3. Backend verifica limitador, utilizador activo e bcrypt.
4. Em sucesso, actualiza último acesso, audita e devolve tokens.
5. Em falha, incrementa o limitador, audita e devolve `401` genérico.
6. Após 5 falhas, devolve `429` durante 15 minutos.

### 6.3 Renovação de sessão

1. Frontend chama `/auth/me` com o access token.
2. Se `401`, tenta `/auth/refresh`.
3. Se o refresh for válido e o utilizador estiver activo, recebe novos tokens e repete `/auth/me`.
4. Caso contrário, limpa a sessão.

### 6.4 Inscrição, pagamento e acesso

1. Aluno autenticado escolhe um curso publicado.
2. `POST /aluno/inscricoes` valida curso, duplicados e termos.
3. Inscrição fica pendente; pagamento é criado conforme o preço.
4. Administração/financeiro valida o comprovativo e confirma o pagamento.
5. Acesso ao conteúdo passa a ser permitido.
6. Progresso é registado por aula.
7. Avaliação é corrigida no backend.
8. Certificado só é emitido quando os requisitos do curso são cumpridos.
9. Certificado pode ser verificado publicamente por código.

### 6.5 Editorial

- Artigos podem ser criados, editados, agendados, publicados e arquivados.
- No arranque da API, artigos agendados vencidos são publicados.
- Eventos suportam inscrição e lista de participantes.
- Campanhas e anúncios têm período e estado.
- Contactos e newsletter são persistidos no backend (contrariamente aos formulários estáticos do frontend actual).

### 6.6 Mercados

- `market_service` mantém cache em memória com TTL.
- Sem `MARKET_*_API_URL/KEY`, os fornecedores não estão configurados.
- O estado é `indisponível`/`não configurado`, com fonte explícita.
- Nenhuma cotação é inventada.
- A administração pode registar cotações manualmente e sincronizar fontes.

---

## 7. Estado de qualidade e validação

### Verificações executadas

| Verificação | Resultado |
| --- | --- |
| `npm.cmd run build` (frontend) | Passou |
| `npm.cmd run lint` (frontend) | Passou |
| `GET http://localhost:8000/api/health` | **Falhou** — servidor indisponível (timeout) |
| Testes automatizados | **Não existem** no repositório |
| `smoke_test.py` | Não executado; requer API activa na porta `8001` |

### Pontos fortes

- Identidade visual coerente e derivada de activos reais.
- Portal preservado e re-tematizado sem reescrita destrutiva.
- Autenticação com validação, mensagens claras e recuperação de sessão.
- Backend com autorização centralizada e regras críticas fora do cliente.
- Modelo de dados abrangente e com restrições de integridade.
- Mercados sem dados fictícios.
- Acessibilidade e movimento reduzido considerados.

### Lacunas e riscos conhecidos

| Prioridade | Lacuna | Impacto |
| --- | --- | --- |
| Alta | Frontend não consome o catálogo/artigos/eventos públicos | Portal mostra estados vazios mesmo com seed publicado |
| Alta | Sem páginas de curso, artigo, evento ou área de aluno no frontend | Fluxo LMS incompleto para o utilizador |
| Alta | Sem painel administrativo no frontend | Gestão depende de API/Swagger |
| Alta | Sem testes automatizados | Regressões não detectadas |
| Alta | `SECRET_KEY` e password de seed são valores de exemplo | Risco se usados em produção |
| Média | Tokens em `localStorage`/`sessionStorage` | Exposição em caso de XSS |
| Média | `smoke_test.py` aponta para `:8001` | Falha contra o servidor predefinido `:8000` |
| Média | Sem endpoints de upload nem serving de `uploads/` | Comprovativos não podem ser carregados/consultados pelo produto |
| Média | Sem recuperação de palavra-passe nem verificação de e-mail | Fluxos de conta incompletos |
| Média | Limitador de login em memória | Não funciona correctamente com múltiplas instâncias |
| Média | Sem `robots.txt`, `sitemap.xml`, canónicos ou `noindex` | SEO e privacidade incompletos |
| Média | `og:image` relativo | Pré-visualização social pode falhar em produção |
| Baixa | Formulários de parceria/newsletter usam `mailto:` | Sem persistência, métricas ou confirmação |
| Baixa | Blocos legais no rodapé, sem páginas próprias | Requisito de privacidade/termos parcialmente cumprido |
| Baixa | Textos de demonstração do seed com imperfeições | Qualidade editorial |
| Baixa | Sem i18n, embora o prompt peça preparação futura | Dívida controlada |
| Baixa | Sem 404 dedicado | Rotas inválidas caem na home |

---

## 8. Próximos passos recomendados

### Fase A — Consolidar o frontend actual

1. Ligar a home a `GET /api/public/home` e `GET /api/public/instituicao`, com estados de carregamento, erro e vazio reais.
2. Criar páginas de catálogo e detalhe de curso (`/cursos`, `/cursos/:slug`).
3. Criar páginas de artigo e evento, com metadados e fontes.
4. Substituir os `mailto:` de parceria/newsletter pelas rotas `POST /public/contactos` e `POST /public/newsletter`.
5. Criar páginas reais de privacidade e termos.
6. Adicionar `robots.txt`, `sitemap.xml`, canónicos e `og:image` absoluto.
7. Introduzir `noindex` nas rotas privadas.

### Fase B — Área de aluno

1. Dashboard com inscrições, progresso, próximas aulas e notificações.
2. Sala de aula com módulos, aulas, materiais e marcação de conclusão.
3. Avaliações com submissão e histórico.
4. Pagamentos e comprovativos.
5. Certificados com página pública de verificação.

### Fase C — Administração

1. Dashboard com métricas reais.
2. Gestão de cursos, módulos, aulas, materiais e turmas.
3. Gestão editorial, eventos, campanhas e anúncios.
4. Gestão de alunos, inscrições e pagamentos.
5. Utilizadores, funções, auditoria e relatórios.
6. Upload de comprovativos com validação de tipo/tamanho e acesso protegido.

### Fase D — Segurança, qualidade e operação

1. Criar suíte `pytest` para autenticação, permissões, inscrição, pagamento, progresso, avaliação e certificados.
2. Corrigir a porta do `smoke_test.py` ou torná-la configurável.
3. Substituir o limitador em memória por Redis em produção.
4. Migrar tokens para cookies seguros ou reforçar CSP.
5. Implementar recuperação de palavra-passe e verificação de e-mail.
6. Configurar logs estruturados, monitorização e backups.
7. Rever conteúdo e credenciais do seed antes de produção.
8. Documentar deploy, variáveis e integrações pendentes.

---

## 9. Comandos úteis

### Frontend

```powershell
cd Front
npm.cmd install
npm.cmd run dev
npm.cmd run build
npm.cmd run lint
npm.cmd run preview
```

Variável opcional em `Front/.env`:

```text
VITE_API_URL=http://localhost:8000/api
```

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

Diagnóstico:

```powershell
python tools/smoke_test.py
```

> Ajustar `BASE` em `tools/smoke_test.py` para `http://127.0.0.1:8000/api` se o servidor estiver na porta predefinida.

Documentação interactiva da API: `http://localhost:8000/docs`.

---

## 10. Convenções do projecto

### Backend

- Código e nomes de domínio em **português** (`nome_completo`, `inscricoes`, `avaliacoes`).
- Rotas em minúsculas, com plural e `snake_case`.
- Schemas Pydantic separados por domínio.
- Serviços para regras de negócio; routers finos.
- Permissões declarativas por rota.
- Migrações versionadas; nunca alterar a base de produção sem autorização.
- Auditoria para operações sensíveis.

### Frontend

- Componentes em `PascalCase`; funções e variáveis em `camelCase`.
- CSS por bloco/componente, com variáveis e prefixos `academy-`, `auth-`, `clop-`.
- Conteúdo institucional centralizado em `config/institution.ts`.
- Cliente HTTP centralizado em `lib/api.ts`.
- Sem dependências novas sem necessidade demonstrada.
- Tipagem estrita; não usar `any` gratuito.
- Respeitar `prefers-reduced-motion`.
- Não apresentar dados fictícios como reais.

### Marca

- Preto `#050505`, ouro `#c9a227`/`#f4cc48`, bronze `#8a6a23`, azeitona `#9aaa47`, creme `#f7f2e6`.
- Serifada para display; sans para interface.
- Movimento subtil, cinematográfico e com propósito.
- Vídeo sempre `muted` quando automático.

---

## 11. Decisões registadas

| Decisão | Justificação |
| --- | --- |
| Preservar o portal existente e re-tematizar | Evita perda de conteúdo e funcionalidades já validadas |
| Router por hash em vez de `react-router` | Zero dependências novas; suficiente para três ecrãs |
| Identidade preto/ouro derivada do logótipo | Fidelidade à marca real, não a uma paleta genérica |
| Vídeo como intro, fundo e hero | Aproveita o activo oficial e cria experiência memorável |
| Autenticação ligada à API existente | Reutiliza backend seguro e evita duplicação |
| Mercados sem números fictícios | Requisito explícito do prompt e integridade institucional |
| Formulários institucionais via `mailto:` | Não inventar persistência enquanto a API pública não está ligada |
| Sem novas dependências npm | Minimiza risco e mantém o build leve |
| Frontend primeiro | Prioridade definida pelo utilizador para esta fase |

---

## 12. Ficheiros-chave

| Ficheiro | Papel |
| --- | --- |
| `Front/src/App.tsx` | Router por hash e títulos |
| `Front/src/main.tsx` | Bootstrap React |
| `Front/src/pages/AcademyHome.tsx` | Portal institucional |
| `Front/src/pages/AuthScreen.tsx` | Login, registo, sessão e intro |
| `Front/src/lib/api.ts` | Cliente HTTP, tokens e refresh |
| `Front/src/components/BrandMark.tsx` | Assinatura visual |
| `Front/src/config/institution.ts` | Identidade e contactos |
| `Front/src/styles/brand.css` | Tokens, marca e keyframes |
| `Front/src/styles/academy.css` | Portal e responsividade |
| `Front/src/styles/auth.css` | Autenticação e intro |
| `Front/index.html` | SEO e metadados |
| `Front/public/brand/*` | Activos oficiais derivados |
| `backend/app/main.py` | Aplicação, CORS, handlers e routers |
| `backend/app/core/config.py` | Configuração |
| `backend/app/core/security.py` | JWT, bcrypt, validação e limitador |
| `backend/app/dependencies/permissions.py` | Matriz de permissões |
| `backend/app/routers/auth.py` | Contratos de autenticação |
| `backend/app/routers/public.py` | Portal público |
| `backend/app/routers/student.py` | Área de aluno |
| `backend/app/routers/admin_*.py` | Administração |
| `backend/app/models/*` | Modelo de dados |
| `backend/app/services/*` | Regras de negócio |
| `backend/seed.py` | Dados iniciais |
| `backend/migrations/versions/fc970855c30f_initial_schema.py` | Migração inicial |
| `backend/tools/smoke_test.py` | Diagnóstico ponta a ponta |

---

## Apêndice A — Prompt mestre original

> O conteúdo seguinte é o prompt originalmente presente neste ficheiro. Foi preservado integralmente como referência de requisitos e não deve ser confundido com o estado actual documentado acima.

---

# PROMPT MASTER — DESENVOLVIMENTO DA CLOP ACADEMY

## 1. PAPEL E OBJECTIVO

Actua como um engenheiro de software sénior, arquitecto de sistemas, especialista em UX/UI, segurança aplicacional, plataformas LMS (Learning Management System), portais financeiros e desenvolvimento de produtos digitais.

A tua missão é analisar o projecto existente no repositório aberto e desenvolver a **CLOP Academy**, plataforma digital oficial da CLOP Academia Digital, LDA., uma instituição angolana orientada para educação financeira, mercados, formação profissional, desenvolvimento pessoal, inteligência artificial, transformação digital e empreendedorismo.

Não te limites a criar uma landing page ou uma demonstração visual. O objectivo é construir uma plataforma funcional, moderna, segura, responsiva e preparada para evoluir em produção.

**Regra principal:** antes de alterar qualquer ficheiro, analisa cuidadosamente o projecto existente. Preserva as funcionalidades, tecnologias e estruturas que já funcionam. Não substituas o projecto inteiro sem necessidade.

---

## 2. IDENTIDADE INSTITUCIONAL

Nome oficial: CLOP Academia Digital, LDA.

Área institucional: Educação Financeira & Mercados.

Assinatura institucional:
“Educação Financeira & Mercados — Conhecimento que transforma oportunidades em resultados.”

A CLOP pretende promover o acesso ao conhecimento, a literacia financeira, a capacitação profissional, a empregabilidade, o empreendedorismo e a inovação digital em Angola.

### Missão
Promover a educação, a literacia financeira, o desenvolvimento de competências e a empregabilidade, através de programas de formação, estágio, orientação profissional e inovação digital.

### Visão
Ser uma instituição de referência em Angola e, progressivamente, no espaço africano, nas áreas da educação financeira, formação profissional, desenvolvimento juvenil e inovação digital.

### Valores
- Integridade e responsabilidade.
- Excelência.
- Inovação.
- Educação e conhecimento.
- Inclusão e igualdade de oportunidades.
- Empreendedorismo.
- Compromisso social.
- Colaboração.

### Áreas de actuação
1. Educação financeira e investimentos.
2. Formação profissional, estágio e plano de carreira.
3. Inteligência artificial e transformação digital.
4. Empreendedorismo e criação de rendimento.
5. Desenvolvimento pessoal e liderança.
6. Comunicação, educação e produção digital.

Usa estes dados como base do conteúdo institucional. Não inventes prémios, parcerias, estatísticas, clientes, resultados, certificações, autorizações financeiras ou informações biográficas.

### Contactos institucionais fornecidos
- Localização: Kinaxixi, Rua da Missão, Edifício 93, Apartamento 8A, Luanda, Angola.
- Unitel: 994 365 4853.
- Africell: 955 517 094.
- E-mail: infocloptrader@gmail.com.

Organiza os contactos num único local de configuração, para permitir a sua alteração futura. Não repitas dados pessoais ou de contacto desnecessariamente noutras partes do código.

---

## 3. PRIMEIRA FASE — AUDITORIA DO PROJECTO

Antes de implementar funcionalidades:

1. Analisa a estrutura completa do repositório.
2. Identifica as tecnologias, frameworks, dependências, rotas, componentes, base de dados e serviços existentes.
3. Verifica os sistemas de autenticação, autorização, validação, uploads, pagamentos e tratamento de erros, se existirem.
4. Identifica as funcionalidades já implementadas, as incompletas e as que estão avariadas.
5. Verifica a responsividade, acessibilidade, segurança e consistência visual.
6. Identifica problemas de configuração, dependências desnecessárias e riscos de compatibilidade.
7. Cria uma lista priorizada de tarefas.

Apresenta um diagnóstico resumido e, em seguida, começa a implementação. Não termines o trabalho depois de apresentar o diagnóstico.

Não recries funcionalidades que já estejam correctamente implementadas. Mantém compatibilidade com a arquitectura existente, salvo se existir uma razão técnica concreta para a alterar.

---

## 4. ARQUITECTURA FUNCIONAL

A plataforma deverá possuir três grandes áreas:

### A. Portal institucional público
Acessível sem autenticação.

Inclui:
- Página inicial.
- Sobre a CLOP.
- Missão, visão e valores.
- Áreas de actuação.
- Formação e cursos.
- Mercados financeiros.
- Notícias e análises.
- Actividades e eventos.
- Projectos e iniciativas.
- Parcerias e oportunidades de colaboração.
- Contactos.
- Autenticação e registo.

### B. Plataforma de aprendizagem — LMS
Acessível aos utilizadores autenticados, de acordo com as respectivas permissões e inscrições.

Inclui:
- Registo e gestão de alunos.
- Catálogo de cursos.
- Inscrição em cursos.
- Gestão de pagamentos e confirmação de inscrições.
- Turmas, módulos e aulas.
- Materiais pedagógicos.
- Vídeos e sessões ao vivo.
- Exercícios, testes e avaliações.
- Acompanhamento do progresso.
- Notificações.
- Certificados, quando os requisitos forem cumpridos.
- Perfil do aluno.

### C. Painel administrativo
Acessível apenas a utilizadores autorizados.

Inclui:
- Dashboard de gestão.
- Gestão institucional.
- Gestão de cursos, turmas, aulas e formadores.
- Gestão de alunos e inscrições.
- Gestão de pagamentos.
- Publicação de notícias e análises.
- Gestão de eventos e actividades.
- Gestão de banners e campanhas publicitárias.
- Gestão de contactos e pedidos recebidos.
- Gestão de utilizadores, funções e permissões.
- Relatórios operacionais.
- Registo de auditoria.

Todas estas áreas devem integrar-se de forma coerente, utilizando as convenções técnicas do projecto existente.

---

## 5. PÁGINA INICIAL — HOME PAGE

Cria uma página inicial institucional com apresentação profissional e forte orientação para conversão.

### Secção 1 — Cabeçalho
- Logótipo CLOP.
- Navegação principal.
- Sobre nós.
- Formação.
- Mercados.
- Notícias.
- Actividades.
- Contactos.
- Botão “Inscrever-se”.
- Botão ou ligação “Área do Aluno”.

O cabeçalho deve funcionar bem em computadores, tablets e telemóveis.

### Secção 2 — Hero institucional
Criar uma composição visual moderna, com título, subtítulo e chamadas para acção.

Mensagem sugerida:

Título:
“Conhecimento financeiro. Competências para o futuro.”

Subtítulo:
“A CLOP Academia Digital promove a educação financeira, a formação profissional e o desenvolvimento de competências para criar novas oportunidades em Angola.”

Chamadas para acção:
- Explorar formações.
- Acompanhar os mercados.
- Conhecer a CLOP.

Utiliza imagens relevantes, tipografia profissional e composição visual consistente. Não sobrecarregues a página com efeitos.

### Secção 3 — Apresentação institucional
Apresentar a CLOP Academia Digital, a sua missão e as principais áreas de actuação.

### Secção 4 — Formações em destaque
Mostrar cursos disponíveis, descrição, duração, modalidade, preço, requisitos e estado das inscrições, quando esses dados estiverem definidos.

Cada curso deve possuir uma página própria.

### Secção 5 — Mercados financeiros
Apresentar um resumo informativo dos mercados internacionais e do mercado angolano.

Incluir data e hora dos dados, identificação das fontes e indicação clara de dados atrasados ou indisponíveis.

Não apresentar valores fictícios como cotações reais.

### Secção 6 — Notícias e análises
Mostrar os artigos mais recentes, com título, imagem, categoria, data, resumo e ligação para o artigo completo.

### Secção 7 — Actividades e eventos
Apresentar eventos futuros, workshops, palestras, conferências e iniciativas da CLOP.

Permitir visualizar os detalhes e efectuar inscrição quando aplicável.

### Secção 8 — Projectos e iniciativas
Apresentar:
- Programa CLOP para Empregabilidade.
- Educação Financeira para Jovens.
- Núcleos de Educação Financeira e Investidores.
- Formação em Inteligência Artificial e Competências Digitais.
- Programas de Estágio e Orientação Profissional.
- Expansão de Parcerias Institucionais.

Identificar claramente iniciativas planeadas, em curso ou concluídas. Não apresentar propostas como projectos já executados.

### Secção 9 — Parcerias
Apresentar as modalidades de colaboração e um formulário para propostas institucionais.

### Secção 10 — Newsletter e rodapé
Implementar inscrição na newsletter com validação e consentimento apropriado.

O rodapé deve conter contactos, páginas institucionais, redes sociais configuráveis, política de privacidade, termos de utilização e avisos legais.

Não inventes contas de redes sociais. Oculta ligações que ainda não estejam configuradas.

---

## 6. PORTAL DE MERCADOS FINANCEIROS

Desenvolve uma área dedicada à educação e informação sobre os mercados financeiros.

### Mercados internacionais
- Bolsas internacionais.
- Índices de referência.
- Forex.
- Matérias-primas.
- Obrigações e outros instrumentos financeiros.
- Calendário económico.
- Indicadores macroeconómicos.
- Notícias e análises educativas.

### Mercado angolano
- BODIVA — Bolsa de Valores e Derivativos de Angola.
- Mercado de dívida pública.
- Obrigações e outros instrumentos negociados.
- Empresas cotadas, quando aplicável.
- Informação institucional.
- Indicadores e dados oficiais disponíveis.
- Educação sobre o funcionamento do mercado de capitais angolano.

### Requisitos técnicos
1. Identifica fontes oficiais e fornecedores de dados adequados.
2. Se já existirem integrações, audita-as antes de modificar.
3. Se não existirem, cria uma arquitectura de integração extensível.
4. Separa os adaptadores de dados do código de apresentação.
5. Guarda a origem, o momento da consulta e o momento da última actualização.
6. Distingue dados em tempo real, atrasados e históricos.
7. Implementa estados de carregamento, ausência de dados e falhas de integração.
8. Usa cache quando apropriado, respeitando as condições de licenciamento das fontes.
9. Nunca inventes cotações, variações percentuais ou notícias.
10. Não exponhas chaves API no frontend nem no repositório.

Não simules uma integração real com dados estáticos apresentados como se fossem actuais. Se uma fonte não estiver configurada, apresenta um estado informativo adequado.

### Notícias e análises financeiras
Criar categorias, pesquisa, filtros, paginação e páginas de detalhe.

Cada artigo deve suportar:
- Título.
- Resumo.
- Conteúdo.
- Autor.
- Categoria.
- Imagem.
- Data de publicação.
- Fonte, quando aplicável.
- Estado de publicação.
- SEO básico.

Distinguir notícias factuais, opinião e conteúdos educativos.

Incluir um aviso de que os conteúdos têm finalidade informativa e educativa e não constituem, por si só, aconselhamento financeiro personalizado.

---

## 7. CATÁLOGO E INSCRIÇÕES NOS CURSOS

Criar um sistema de formação funcional.

### Catálogo público
Cada curso deve apresentar:
- Nome.
- Descrição.
- Objectivos.
- Conteúdo programático.
- Duração.
- Modalidade.
- Requisitos.
- Formador, se atribuído.
- Preço, se aplicável.
- Datas.
- Estado das inscrições.
- Botão de inscrição.

Os cursos devem ser geridos pela administração e não ficar limitados a dados escritos directamente nos componentes.

### Processo de inscrição
Implementar o seguinte fluxo:

1. O visitante abre a página do curso.
2. Selecciona “Inscrever-se”.
3. Se não tiver conta, cria uma conta; caso contrário, inicia sessão.
4. Preenche os dados necessários.
5. Aceita os termos aplicáveis.
6. Confirma a inscrição.
7. Se houver pagamento, segue para o método configurado.
8. O sistema regista o estado da inscrição e do pagamento.
9. Após confirmação válida e cumprimento dos requisitos, o aluno recebe acesso ao curso.
10. O aluno recebe uma notificação com o resultado do processo.

Prevenir inscrições duplicadas, manipulação de preços e acesso indevido a cursos pagos.

Não conceder acesso com base apenas numa confirmação visual do frontend.

### Gestão de pagamentos
Implementar uma camada de pagamentos extensível.

Se o projecto não possuir um provedor de pagamento funcional, preparar a estrutura e a interface administrativa sem fingir que os pagamentos foram processados.

Permitir confirmação manual por administrador autorizado, com comprovativo quando necessário, histórico e registo de auditoria.

Validar sempre os pagamentos no backend. Nunca confiar exclusivamente no estado enviado pelo cliente.

---

## 8. ÁREA DO ALUNO

Criar um painel de aprendizagem com navegação simples.

### Dashboard
Apresentar:
- Cursos inscritos.
- Cursos em andamento.
- Progresso por curso.
- Próximas aulas.
- Avaliações pendentes.
- Notificações.
- Eventos relevantes.

### Sala de aulas
Permitir:
- Consultar módulos e aulas.
- Reproduzir vídeos.
- Abrir materiais disponibilizados.
- Participar em sessões ao vivo.
- Marcar aulas como concluídas.
- Retomar a aprendizagem.
- Consultar exercícios e avaliações.

O acesso aos conteúdos deve respeitar a inscrição, o estado da conta e as permissões do utilizador.

### Avaliações
Implementar, conforme a arquitectura existente:
- Exercícios.
- Testes com perguntas.
- Registo de submissões.
- Classificação.
- Feedback.
- Histórico de resultados.

A lógica de avaliação e os resultados finais devem ser validados no backend.

### Certificados
Criar certificados apenas após a verificação dos requisitos definidos para cada curso.

Os certificados devem possuir identificador único e uma página de verificação pública que revele apenas os dados estritamente necessários.

Não emitir certificados automaticamente apenas porque o aluno abriu todas as aulas.

### Perfil
Permitir actualizar os dados autorizados, consultar inscrições e acompanhar o histórico da formação.

---

## 9. PAINEL ADMINISTRATIVO

Criar um painel administrativo protegido.

### Dashboard administrativo
Apresentar métricas obtidas da base de dados:
- Número de alunos registados.
- Inscrições por curso.
- Cursos activos.
- Pagamentos pendentes e confirmados.
- Publicações.
- Eventos.
- Pedidos de contacto.

Não utilizar números inventados para preencher cartões estatísticos.

### Gestão de cursos
Permitir criar, editar, publicar, arquivar e gerir:
- Cursos.
- Módulos.
- Aulas.
- Materiais.
- Turmas.
- Formadores.
- Preços e inscrições.
- Requisitos de conclusão.

### Gestão editorial
Permitir criar, editar, agendar, publicar e arquivar:
- Notícias.
- Análises.
- Artigos educativos.
- Eventos.
- Páginas institucionais.
- Banners.
- Campanhas publicitárias.

### Gestão de inscrições e pagamentos
Permitir pesquisar alunos, consultar inscrições, validar comprovativos, alterar estados de forma autorizada e consultar o histórico de operações.

### Gestão de utilizadores
Implementar permissões de acordo com funções.

Não atribuir privilégios administrativos a utilizadores comuns.

### Auditoria
Registar as operações sensíveis, incluindo alterações de permissões, confirmações de pagamentos, emissão de certificados e mudanças de estado de inscrições.

---

## 10. PUBLICIDADE, CAMPANHAS E ACTIVIDADES

A plataforma deve funcionar também como canal de divulgação da CLOP.

Implementar:
- Banners institucionais.
- Campanhas de inscrição.
- Divulgação de novos cursos.
- Promoção de eventos.
- Anúncios de parcerias.
- Espaços publicitários configuráveis.
- Páginas de detalhe para eventos.
- Formulários de inscrição em eventos.
- Gestão do período de publicação.
- Estado activo ou inactivo.
- Métricas básicas de visualizações e cliques, respeitando a privacidade.

A administração deve controlar quais campanhas aparecem na página inicial e em cada área do portal.

Evitar publicidade intrusiva, pop-ups excessivos e anúncios que comprometam a credibilidade institucional.

---

## 11. DESIGN E EXPERIÊNCIA DO UTILIZADOR

O resultado deve ter aparência de uma instituição financeira e educativa moderna.

### Direcção visual
- Identidade visual profissional e consistente.
- Paleta baseada em azul-escuro, branco e tons neutros, ajustável à identidade oficial da CLOP.
- Tipografia legível.
- Hierarquia visual clara.
- Fotografias relevantes e de qualidade.
- Ícones consistentes.
- Gráficos financeiros legíveis.
- Cartões discretos.
- Espaçamento adequado.
- Animações subtis.
- Formulários simples e claros.

Não utilizar gradientes excessivos, emojis decorativos em toda a interface, efeitos exagerados, componentes gigantes ou padrões visuais genéricos que façam o site parecer um template automático.

### Responsividade
Garantir boa utilização em:
- Computadores.
- Tablets.
- Telemóveis Android.
- Ecrãs de diferentes dimensões.

### Acessibilidade
Implementar:
- Navegação por teclado.
- Contraste adequado.
- Etiquetas nos formulários.
- Textos alternativos.
- Estados de foco visíveis.
- Mensagens de erro compreensíveis.
- Estrutura semântica.
- Compatibilidade razoável com leitores de ecrã.

### Idioma
Português de Angola, com terminologia e grafia consistentes.

Preparar a aplicação para internacionalização futura, sem tornar a implementação inicial desnecessariamente complexa.

---

## 12. ARQUITECTURA E MODELO DE DADOS

Adapta o modelo de dados à tecnologia e à base de dados existentes.

Quando necessário, considera entidades equivalentes a:

- Users.
- Roles e Permissions.
- StudentProfiles.
- Courses.
- CourseModules.
- Lessons.
- LessonMaterials.
- Enrollments.
- Classes ou Cohorts.
- Assessments.
- Questions.
- Submissions.
- ProgressRecords.
- Payments.
- PaymentReceipts.
- Certificates.
- Articles.
- Categories.
- Events.
- EventRegistrations.
- Campaigns.
- Advertisements.
- ContactMessages.
- NewsletterSubscriptions.
- Notifications.
- AuditLogs.

Não cries tabelas redundantes nem dupliques entidades já existentes.

Implementa:
- Chaves e relações coerentes.
- Restrições de integridade.
- Índices adequados.
- Migrações versionadas.
- Validação dos dados.
- Paginação nas listagens.
- Transacções nas operações críticas.
- Registos temporais consistentes.

Usa as convenções de nomes já adoptadas pelo projecto.

---

## 13. SEGURANÇA

A segurança deve ser implementada desde o início.

- Autenticação robusta.
- Hash seguro de palavras-passe.
- Autorização no backend.
- Protecção das rotas e recursos privados.
- Validação dos dados recebidos.
- Protecção contra SQL injection.
- Protecção contra XSS e CSRF, conforme o mecanismo de autenticação.
- Limitação de tentativas de autenticação.
- Gestão segura de sessões ou tokens.
- CORS restritivo.
- Validação de ficheiros enviados.
- Limites de tamanho de uploads.
- Segredos apenas em variáveis de ambiente.
- Logs sem palavras-passe, tokens ou outros segredos.
- Protecção contra acesso horizontal indevido a dados de outros alunos.
- Políticas de privacidade e retenção de dados.
- Registo de auditoria para operações críticas.

Se existir autenticação por cookies, configura adequadamente as opções de segurança. Se forem utilizados tokens, evita armazenamento e exposição desnecessários.

Não exponhas comprovativos de pagamento, dados pessoais ou materiais privados através de URLs públicas previsíveis.

---

## 14. SEO E PRESENÇA DIGITAL

Implementar:
- Títulos e descrições por página.
- URLs legíveis.
- Sitemap.
- Robots.txt.
- Metadados Open Graph.
- Imagens optimizadas.
- URLs canónicas quando apropriado.
- Dados estruturados apenas quando correctos.
- Páginas de detalhe indexáveis para notícias, cursos e eventos públicos.
- Exclusão das áreas privadas da indexação.

Optimizar o desempenho e a experiência em redes móveis, considerando as condições de conectividade em Angola.

---

## 15. TESTES E QUALIDADE

Criar ou actualizar testes para os fluxos mais importantes.

No mínimo, testar:
- Registo e autenticação.
- Permissões.
- Inscrição num curso.
- Prevenção de inscrições duplicadas.
- Pagamentos e confirmação.
- Acesso às aulas.
- Registo do progresso.
- Avaliações.
- Emissão e verificação de certificados.
- Publicação de notícias.
- Gestão de eventos.
- Protecção dos endpoints administrativos.

Executar os testes, o lint e a compilação disponíveis no projecto.

Corrigir os erros introduzidos pela implementação. Não afirmar que tudo está funcional se os testes não tiverem sido executados ou se existirem dependências externas por configurar.

---

## 16. REGRAS DE EXECUÇÃO NO OPENCODE

Segue esta ordem de trabalho:

### Fase 1 — Auditoria
Inspeccionar o repositório, compreender a arquitectura e identificar o estado actual.

### Fase 2 — Planeamento
Definir módulos, rotas, alterações de base de dados e prioridades.

### Fase 3 — Implementação do portal público
Construir a estrutura institucional, páginas, navegação e conteúdos.

### Fase 4 — Formação
Implementar cursos, inscrições, autenticação e área do aluno.

### Fase 5 — Administração
Implementar a gestão de conteúdos, alunos, eventos, campanhas e pagamentos.

### Fase 6 — Mercados financeiros
Implementar o portal de informação e as integrações de dados disponíveis.

### Fase 7 — Segurança e testes
Verificar permissões, dados, erros, testes e desempenho.

### Fase 8 — Documentação
Actualizar o README com:
- Arquitectura.
- Pré-requisitos.
- Instalação.
- Variáveis de ambiente.
- Migrações.
- Criação do primeiro administrador.
- Execução local.
- Testes.
- Build e deploy.
- Integrações externas pendentes.

Implementa cada fase de forma incremental, validando o resultado antes de avançar.

Se o projecto for demasiado grande para uma única execução, prioriza uma versão funcional de ponta a ponta e documenta o trabalho restante.

Não pares para pedir autorização a cada pequena decisão técnica. Toma decisões razoáveis, regista as decisões importantes e pede esclarecimentos apenas quando faltar informação essencial ou existir risco significativo de perda de dados.

Nunca apagues dados reais, reescrevas o histórico Git, substituas configurações de produção ou executes migrações destrutivas sem autorização explícita.

Não deixes botões sem acção, formulários fictícios, páginas vazias apresentadas como concluídas, dados financeiros falsos ou funcionalidades simuladas sem indicação clara.

---

## 17. CRITÉRIOS DE ACEITAÇÃO

O trabalho será considerado satisfatório quando:

1. O portal institucional estiver completo e navegável.
2. Os conteúdos reflectirem a identidade oficial da CLOP Academia Digital.
3. Os visitantes conseguirem consultar cursos e iniciar inscrições.
4. Os alunos conseguirem autenticar-se e aceder aos cursos autorizados.
5. A administração conseguir gerir cursos, alunos, publicações e eventos.
6. O fluxo de pagamentos tiver validação segura ou estiver claramente identificado como dependente de configuração externa.
7. O portal de mercados estiver preparado para dados reais, com fontes e estados de actualização explícitos.
8. As permissões forem aplicadas no backend.
9. A interface funcionar em dispositivos móveis.
10. Os principais testes forem executados e os resultados documentados.
11. As instruções de instalação e configuração estiverem actualizadas.
12. As funcionalidades externas que ainda dependam de credenciais, licenças ou contratos estiverem claramente documentadas.

## 18. RELATÓRIO FINAL

No final, apresenta:
- O que foi implementado.
- Os ficheiros e módulos principais alterados.
- As funcionalidades que estão operacionais.
- Os testes executados e respectivos resultados.
- As variáveis de ambiente necessárias.
- As integrações externas pendentes.
- Os problemas conhecidos.
- As próximas tarefas recomendadas.

**Começa agora por auditar o repositório aberto, identifica a arquitectura existente e implementa a CLOP Academy de forma incremental, profissional, segura e funcional.**