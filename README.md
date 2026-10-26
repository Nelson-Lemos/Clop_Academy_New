# Clop_Academy_New

CLOP Academy — plataforma de formação (frontend React/Vite + backend FastAPI),
com base de dados PostgreSQL na Neon.

## Estrutura

- `Front/` — SPA React + Vite (compilada para `Front/dist`).
- `backend/` — API FastAPI + SQLAlchemy + Alembic.
- `neon.ts` — política de serviços Neon (Postgres) gerida pela CLI.
- `.env.local` — variáveis injetadas por `neon deploy` (não versionado).

## Neon

O projeto está ligado ao projeto Neon `clop_academy`
(`gentle-wildflower-96324936`, branch `production`). Para provisionar e puxar
as credenciais:

```bash
neon deploy
```

Isto escreve `DATABASE_URL` (pooled), `DATABASE_URL_UNPOOLED` (direto) e
`NEON_BRANCH` em `.env.local`.

O backend lê primeiro `backend/.env` e depois `.env.local` da raiz, que tem
precedência. A aplicação usa o URL pooled (PgBouncer em modo transacção, com
prepared statements desativados no psycopg 3); o Alembic usa o URL direto.

## Deploy (Vercel + Render)

O `render.yaml` configura a API FastAPI no Render com Python, health check,
ligação à base de dados e migrações Alembic antes do arranque. Para criar o
serviço, no Render escolha **New → Blueprint**, ligue este repositório e
confirme o Blueprint. Quando pedido, introduza:

- `DATABASE_URL`: URL pooled da branch Neon `production`.
- `DATABASE_URL_UNPOOLED`: URL direto da mesma branch, usado pelo Alembic.
- `SECRET_KEY`: segredo aleatório forte, gerado localmente.
- `SEED_ADMIN_PASSWORD`: palavra-passe forte para o administrador criado pelo
  script `backend/seed.py`. Não reutilize a palavra-passe de exemplo.

Os valores `sync: false` são introduzidos no painel do Render e não ficam no
repositório. O comando de arranque corre `alembic upgrade head` antes de
iniciar o servidor em `0.0.0.0:$PORT`; o health check valida `/api/health`.
No plano gratuito, as migrações repetem-se em cada arranque; o Alembic só
aplica revisões ainda pendentes.
O Blueprint não cria automaticamente o administrador: depois da primeira
migração, execute `python seed.py --sem-demo` uma vez num ambiente confiável
com as variáveis de produção. Não execute `python seed.py` em produção, pois
esse comando também cria conteúdo de demonstração.

Depois do primeiro deploy da API, copie o domínio público atribuído pelo Render
(por exemplo, `https://clop-academy-api.onrender.com`). No projeto da Vercel,
adicione `VITE_API_URL` com esse domínio seguido de `/api`, em Production e
Preview, e faça um novo deploy do frontend. Configure a raiz do projeto Vercel
como `Front`, com o comando de build `npm run build` e a pasta de saída `dist`.
O build da Vercel falha intencionalmente se `VITE_API_URL` estiver em falta,
inválido ou apontar para `localhost`, em vez de publicar uma versão sem acesso
à API. O domínio de produção da Vercel
`https://clop-academy.vercel.app` já está configurado em `CORS_ORIGINS` e
`PUBLIC_SITE_URL` no Blueprint.

Não coloque URLs de ligação, segredos ou palavras-passe em ficheiros
versionados, no frontend ou em mensagens. O `backend/.env` local é apenas para
desenvolvimento e não é usado para configurar as variáveis do Render.

## Desenvolvimento

Backend (a partir de `backend/`):

```bash
python -m alembic upgrade head
python seed.py
python -m uvicorn app.main:app --reload --port 8000
```

Frontend (a partir da raiz):

```bash
npm install --prefix Front
npm run dev
```

Build de produção (raiz):

```bash
npm run build
```

## Variáveis de ambiente

- `backend/.env.example` — modelo das variáveis do backend.
- `.env.local` — gerado pela Neon; nunca versionar.
