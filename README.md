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
