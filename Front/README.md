# CLOP Academy — Frontend

Portal institucional e ponto de entrada de autenticação da **CLOP Academia Digital, LDA.**, instituição angolana de educação financeira, mercados, formação profissional e inovação digital.

Este frontend é **independente do CLOP ERP**, com aplicação, dependências, build e ciclo de publicação próprios.

## Estado actual

- Portal institucional responsivo, re-tematizado a partir do logótipo e do vídeo oficiais da CLOP.
- Identidade visual preto/ouro com emblema (touro, escudo e torres), tipografia serifada e movimento subtil.
- Ecrãs de **entrar** e **criar conta** com introdução cinematográfica, validação de formulário e integração com a API FastAPI.
- Sessão com access token, refresh token, cache de utilizador e renovação automática.
- Formulários de parceria e newsletter abrem o cliente de e-mail do visitante; não persistem dados.
- Catálogo, artigos, eventos, área de aluno e administração ainda **não estão implementados** neste frontend.
- Dados de mercado são apresentados como indisponíveis enquanto não existir uma fonte configurada. Não são mostradas cotações fictícias.

## Identidade e activos

A identidade visual foi derivada dos activos oficiais da marca. O vídeo é servido directamente de `public/brand/clop-brand-film.mp4`.

| Activo | Uso |
| --- | --- |
| `public/brand/clop-logo.jpg` | Logótipo original |
| `public/brand/clop-lockup.png` | Assinatura completa transparente |
| `public/brand/clop-emblem.png` | Emblema, favicon e marca de água |
| `public/brand/clop-brand-film.mp4` | Intro, fundo de autenticação e hero |
| `public/brand/clop-brand-poster.jpg` | Poster dos vídeos |
| `public/brand/clop-og.jpg` | Open Graph / Twitter Card |

Paleta principal: preto `#050505`, ouro `#c9a227` / `#f4cc48`, bronze `#8a6a23`, azeitona `#9aaa47` e creme `#f7f2e6`.

Os tokens e keyframes globais estão em `src/styles/brand.css`. O vídeo é sempre reproduzido sem som (`muted`) para permitir autoplay.

## Rotas

O routing é feito por `window.location.hash`, sem `react-router`:

| Rota | Ecrã |
| --- | --- |
| `#/` ou qualquer hash de âncora | Portal institucional |
| `#/entrar` | Login |
| `#/registar` | Registo de aluno |

Âncoras do portal: `#inicio`, `#sobre`, `#areas`, `#formacao`, `#mercados`, `#actualidade`, `#iniciativas`, `#parcerias`, `#actualizacoes`, `#contactos`, `#privacidade` e `#termos`.

## Autenticação

O cliente da API está em `src/lib/api.ts`.

```text
VITE_API_URL=http://localhost:8000/api
```

Se a variável não estiver definida, o valor por omissão é `http://localhost:8000/api`.

Endpoints utilizados:

- `POST /auth/login`
- `POST /auth/registo`
- `POST /auth/refresh`
- `GET /auth/me`

Comportamento da sessão:

- “Manter sessão neste dispositivo” guarda os tokens em `localStorage`; caso contrário, usa `sessionStorage`.
- Chaves: `clop:access`, `clop:refresh` e `clop:user`.
- Em `401` ao validar `/auth/me`, o cliente tenta renovar a sessão com `/auth/refresh`.
- “Terminar sessão” limpa os tokens e a cache localmente.
- Erros da API são apresentados em português; falhas de rede não expõem detalhes internos.

A introdução animada é mostrada uma vez por sessão do navegador (`sessionStorage: clop:intro-seen`) e pode ser saltada.

> A autenticação real depende de o backend e o MySQL estarem activos. Sem eles, o ecrã apresenta uma mensagem de indisponibilidade.

## Tecnologias

- React 19 + TypeScript (modo `strict`)
- Vite 8
- `lucide-react` para ícones
- CSS puro com variáveis
- `oxlint` para lint

Não existem dependências de routing, estado global ou UI kit.

## Execução local

Requisitos: Node.js 20.19+ e npm.

```powershell
npm.cmd install
npm.cmd run dev
```

O servidor Vite escuta em `0.0.0.0:5173`. Para abrir noutro dispositivo ligado à mesma rede Wi-Fi ou LAN, aceda a `http://IP-DO-COMPUTADOR:5173`. No Windows, descubra o endereço IPv4 com `ipconfig` na ligação activa. Se necessário, permita o Node.js na firewall do Windows para redes privadas.

> Neste ambiente Windows/PowerShell, o shim `npm` pode estar bloqueado. Use `npm.cmd`.

Build, lint e pré-visualização:

```powershell
npm.cmd run build
npm.cmd run lint
npm.cmd run preview
```

A pré-visualização escuta em `0.0.0.0:4173`.

Para testar a autenticação, inicie também a API:

```powershell
cd ../backend
uvicorn app.main:app --reload --port 8000
```

## Estrutura

```text
src/
├─ main.tsx                 # bootstrap React
├─ App.tsx                  # router por hash
├─ components/BrandMark.tsx # assinatura CLOP
├─ config/institution.ts    # identidade, contactos e pilares
├─ lib/api.ts               # cliente HTTP, tokens e refresh
├─ pages/AcademyHome.tsx    # portal institucional
├─ pages/AuthScreen.tsx     # login, registo e intro
└─ styles/
   ├─ brand.css             # tokens, marca e keyframes
   ├─ academy.css           # portal
   └─ auth.css              # autenticação
```

## Acessibilidade

- Navegação por teclado e foco visível.
- Etiquetas em todos os campos e mensagens de erro com `aria-live`/`role="alert"`.
- Menu móvel com `aria-expanded` e `aria-controls`.
- Emblemas decorativos com texto alternativo vazio; links com rótulo.
- `prefers-reduced-motion` desactiva animações e scroll suave.
- Contraste e hierarquia pensados para leitura em ecrãs pequenos.

## Limitações e próximos passos

1. Ligar o portal a `/api/public/home`, `/api/public/instituicao`, cursos, artigos e eventos.
2. Criar páginas de catálogo e detalhe de curso.
3. Implementar a área de aluno (dashboard, aulas, progresso, avaliações, certificados).
4. Implementar o painel administrativo.
5. Substituir os formulários `mailto:` pelas rotas `POST /public/contactos` e `POST /public/newsletter`.
6. Criar páginas próprias de privacidade e termos.
7. Adicionar `robots.txt`, `sitemap.xml`, canónicos e metadados sociais absolutos.
8. Rever o armazenamento de tokens e reforçar a política de segurança em produção.

Para a análise completa do projecto (frontend, backend, modelo de dados, permissões e roadmap), consulte `../agent.md`.
