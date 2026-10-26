"""Populamento inicial da base de dados da CLOP Academy.

Executa de forma idempotente: pode ser executado várias vezes sem duplicar
conteúdo.

Conteúdo de demonstração (cursos, artigos, eventos) é claramente identified
na descrição como material de exemplo. Nunca são criados preços de parceiros,
estatísticas, prémios ou certificações fictícias.

Uso:

    python seed.py            # cria o administrador e o conteúdo de exemplo
    python seed.py --sem-demo # apenas o primeiro administrador
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password, normalize_email
from app.core.utils import slugify
from app.models.catalog import (
    Cohort,
    Course,
    CourseModule,
    CourseStatus,
    Lesson,
    LessonMaterial,
)
from app.models.content import (
    Article,
    ArticleStatus,
    ArticleType,
    Campaign,
    CampaignStatus,
    Category,
    Event,
    EventStatus,
    Project,
    ProjectStatus,
)
from app.models.enrollment import Assessment, AssessmentType, Question
from app.models.user import InstructorProfile, User, UserRole, UserStatus


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def garantir_admin(db: Session) -> User:
    """Cria (ou actualiza) o primeiro administrador a partir das variáveis de ambiente."""
    email = normalize_email(settings.SEED_ADMIN_EMAIL)
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        user = User(
            nome_completo=settings.SEED_ADMIN_NAME or "Administrador CLOP",
            email=email,
            password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
            role=UserRole.SUPERADMIN,
            estado=UserStatus.ACTIVE,
            aceite_termos_em=_agora(),
        )
        db.add(user)
        db.flush()
        print(f"[+] Administrador criado: {email}")
    else:
        changed = False
        if user.role != UserRole.SUPERADMIN:
            user.role = UserRole.SUPERADMIN
            changed = True
        if user.estado != UserStatus.ACTIVE:
            user.estado = UserStatus.ACTIVE
            changed = True
        if changed:
            db.flush()
            print(f"[~] Administrador actualizado: {email}")
        else:
            print(f"[=] Administrador já existe: {email}")

    return user


def garantir_categorias(db: Session) -> dict[str, Category]:
    dados = [
        ("Mercados Financeiros", "Mercados e instrumentos de investimento."),
        ("Educação Financeira", "Literacia financeira e gestão de finanças pessoais."),
        ("Tecnologia e IA", "Transformação digital e inteligência artificial."),
        ("Empreendedorismo", "Criação de negócios e geração de rendimento."),
        ("Desenvolvimento Profissional", "Carreira, comunicação e liderança."),
        ("Notícias da Instituição", "Comunicados e novidades da CLOP."),
    ]

    categorias: dict[str, Category] = {}
    for nome, descricao in dados:
        slug = slugify(nome)
        categoria = db.query(Category).filter(Category.slug == slug).first()
        if categoria is None:
            categoria = Category(nome=nome, slug=slug, descricao=descricao)
            db.add(categoria)
            db.flush()
        categorias[nome] = categoria
    db.flush()
    return categorias


def garantir_formador(db: Session) -> User:
    email = "formacao@clop.academy"
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user

    user = User(
        nome_completo="Equipa de Formação CLOP",
        email=email,
        password_hash=hash_password("Formacao_Clop_2026!"),
        role=UserRole.INSTRUCTOR,
        estado=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    db.add(
        InstructorProfile(
            user_id=user.id,
            cargo="Formação e Capacitação",
            bio=(
                "Equipa de formadores da CLOP Academia Digital, LDA., "
                "responsável pela concepção e lecção dos cursos de educação "
                "financeira, mercados e transformação digital."
            ),
        )
    )
    db.flush()
    print("[+] Formador de demonstração criado.")
    return user


CURSOS_DEMO = [
    {
        "nome": "Literacia Financeira — Fundamentos",
        "area": "Educação Financeira",
        "descricao_resumida": (
            "Aprenda a organizar o seu orçamento, poupar com método e tomar "
            "decisões financeiras mais seguras."
        ),
        "descricao": (
            "Curso de introdução à educação financeira dirigido a quem quer "
            "assumir o controlo das suas finanças pessoais. Percorre o "
            "planeamento do orçamento familiar, a poupança, o crédito, os "
            "seguros e a leitura básica de produtos de investimento. "
            "Conteúdo de demonstração para illustrates a estrutura da "
            "plataforma."
        ),
        "objetivos": (
            "- Elaborar um orçamento familiar mensal\n"
            "- Distinguir poupança, investimento e crédito\n"
            "- Reconhecer custos e riscos de produtos financeiros\n"
            "- Definir objectivos financeiros com prazos"
        ),
        "conteudo_programatico": (
            "1. Os seus números\n2. Orçamento e controlo de despesas\n"
            "3. Poupança e fundo de emergência\n4. Crédito e endividamento\n"
            "5. Seguros e protecção\n6. Introdução ao investimento"
        ),
        "requisitos": "Nenhum pré-requisito. Curso aberto a todos os públicos.",
        "modalidade": "ONLINE",
        "nivel": "INICIADO",
        "duracao_horas": 12,
        "numero_aulas": 6,
        "preco": "45000.00",
        "percentagem_conclusao_minima": 100,
        "aulas_obrigatorias_minimas": 6,
        "modulos": [
            (
                "Fundamentos de gestão financeira",
                "Como ler os próprios números antes de decidir.",
                [
                    (
                        "Aula 1 — Os seus números",
                        "Como recolher e organizar a informação financeira pessoal.",
                        "VIDEO",
                        35,
                    ),
                    (
                        "Aula 2 — Orçamento familiar mensal",
                        "Construção de um orçamento simples e sustentável.",
                        "VIDEO",
                        45,
                    ),
                    (
                        "Aula 3 — Fundo de emergência",
                        "Quanto guardar, para que e como automatizar.",
                        "VIDEO",
                        30,
                    ),
                ],
            ),
            (
                "Protecção e primeiros passos no investimento",
                "Gerir riscos antes de buscar rendimento.",
                [
                    (
                        "Aula 4 — Crédito e endividamento",
                        "Custo real do crédito e como evitar a sobre-endividamento.",
                        "VIDEO",
                        40,
                    ),
                    (
                        "Aula 5 — Seguros e protecção",
                        "Coberturas essenciais e leitura de apólices.",
                        "VIDEO",
                        30,
                    ),
                    (
                        "Aula 6 — Introdução ao investimento",
                        "Classes de activos, risco e prazo.",
                        "VIDEO",
                        40,
                    ),
                ],
            ),
        ],
        "avaliacao": {
            "titulo": "Teste — Fundamentos de literacia financeira",
            "descricao": "Verificação de conhecimentos sobre orçamento e poupança.",
            "perguntas": [
                (
                    "Qual é a primeira regra de um orçamento mensal eficaz?",
                    [
                        "Registar todas as receitas e despesas",
                        "Investir primeiro",
                        "Não pagar dívidas",
                        "Guardar 50% do salário",
                    ],
                    "Registar todas as receitas e despesas",
                ),
                (
                    "Qual a principal função de um fundo de emergência?",
                    [
                        "Aumentar o rendimento",
                        "Pagar dívidas",
                        "Cobrir imprevistos",
                        "Financiar viagens",
                    ],
                    "Cobrir imprevistos",
                ),
                (
                    "Ao comparar um crédito, o que deve ser avaliado primeiro?",
                    [
                        "A TAEG",
                        "A cor do cartão",
                        "O nome do banco",
                        "A idade do devedor",
                    ],
                    "A TAEG",
                ),
            ],
        },
    },
    {
        "nome": "Leitura de Mercados para Não Especialistas",
        "area": "Mercados Financeiros",
        "descricao_resumida": (
            "Entenda índices, taxas de juro, câmbio e IndicatorGiving de "
            "risco sem perder o fio."
        ),
        "descricao": (
            "Curso de introdução à leitura dos mercados financeiros. Explica a "
            "lógica por trás dos índices, a relação entre inflação e taxas de "
            "juro, o comportamento do câmbio em Angola e os principais "
            "indicadores macroeconómicos. Conteúdo de demonstração."
        ),
        "objetivos": (
            "- Identificar a diferença entre preço e valor\n"
            "- Interpretar variações percentuais\n"
            "- Relacionar política monetária e mercado\n"
            "- Reconhecer limites da análise técnica"
        ),
        "conteudo_programatico": (
            "1. Como funciona um mercado\n2. Índices e composição\n"
            "3. Taxas de juro e inflação\n4. Câmbio e risco cambial\n"
            "5. Indicadores macro-económicos"
        ),
        "requisitos": "Conhecimentos básicos de economia doméstica são suficientes.",
        "modalidade": "ONLINE",
        "nivel": "INTERMEDIO",
        "duracao_horas": 10,
        "numero_aulas": 5,
        "preco": "60000.00",
        "percentagem_conclusao_minima": 80,
        "aulas_obrigatorias_minimas": 5,
        "modulos": [
            (
                "Fundamentos dos mercados",
                "A anatomia de um mercado financeiro.",
                [
                    (
                        "Aula 1 — Como funciona um mercado",
                        "Participantes, unidades de conta e formação de preços.",
                        "VIDEO",
                        40,
                    ),
                    (
                        "Aula 2 — Índices e composição",
                        "Como se constrói um índice e porque importa.",
                        "VIDEO",
                        45,
                    ),
                ],
            ),
            (
                "Macroeconomia e risco",
                "As variáveis que movem os preços.",
                [
                    (
                        "Aula 3 — Taxas de juro e inflação",
                        "A relação entre política monetária e preços.",
                        "VIDEO",
                        40,
                    ),
                    (
                        "Aula 4 — Câmbio e risco cambial",
                        "O que move o kwanza e como avaliar o risco.",
                        "VIDEO",
                        35,
                    ),
                    (
                        "Aula 5 — Indicadores macro-económicos",
                        "PIB, inflação, desemprego e dívida: o que observar.",
                        "VIDEO",
                        35,
                    ),
                ],
            ),
        ],
    },
    {
        "nome": "Inteligência Artificial Aplicada ao Negócio",
        "area": "Tecnologia e IA",
        "descricao_resumida": (
            "Use a IA para automatizar tarefas, analisar dados e criar "
            "vantagem competitiva no dia-a-dia da sua organização."
        ),
        "descricao": (
            "Curso prático sobre a aplicação da inteligência artificial em "
            "pequenos e médios negócios: automatização de rotinas, apoio à "
            "decisão, análise de dados e comunicação assistida por IA. "
            "Conteúdo de demonstração."
        ),
        "objetivos": (
            "- Identificar tarefas automatizáveis no seu fluxo de trabalho\n"
            "- Usar assistentes de IA com criterio e verificação\n"
            "- Analisar dados simples com apoio de ferramentas\n"
            "- Aplicar regras de uso responsável"
        ),
        "conteudo_programatico": (
            "1. O que é (e o que não é) IA\n2. Automações do dia-a-dia\n"
            "3. Dados e análise assistida\n4. Uso responsável"
        ),
        "requisitos": "Utilização básica de computador.",
        "modalidade": "HIBRIDO",
        "nivel": "INICIADO",
        "duracao_horas": 8,
        "numero_aulas": 4,
        "preco": "55000.00",
        "percentagem_conclusao_minima": 100,
        "aulas_obrigatorias_minimas": 4,
        "modulos": [
            (
                "IA na prática",
                "Do conceito à operação diária.",
                [
                    (
                        "Aula 1 — O que é (e o que não é) IA",
                        "Capacidades, limites e expectativas realistas.",
                        "VIDEO",
                        35,
                    ),
                    (
                        "Aula 2 — Automações do dia-a-dia",
                        "Que tarefas da sua rotina podem ser assistidas.",
                        "VIDEO",
                        40,
                    ),
                ],
            ),
            (
                "Dados, decisão e responsabilidade",
                "Transformar dados em decisões defensáveis.",
                [
                    (
                        "Aula 3 — Dados e análise assistida",
                        "Indicadores simples para decisões do dia-a-dia.",
                        "VIDEO",
                        40,
                    ),
                    (
                        "Aula 4 — Uso responsável",
                        "Privacidade, verificação e limites de uso.",
                        "VIDEO",
                        30,
                    ),
                ],
            ),
        ],
    },
]


def garantir_cursos(db: Session, formador: User, categorias: dict[str, Category]) -> None:
    for definicao in CURSOS_DEMO:
        slug = slugify(definicao["nome"])
        curso = db.query(Course).filter(Course.slug == slug).first()
        if curso is not None:
            print(f"[=] Curso já existe: {curso.nome}")
            continue

        curso = Course(
            nome=definicao["nome"],
            slug=slug,
            descricao_resumida=definicao["descricao_resumida"],
            descricao=definicao["descricao"],
            objetivos=definicao["objetivos"],
            conteudo_programatico=definicao["conteudo_programatico"],
            requisitos=definicao["requisitos"],
            modalidade=definicao["modalidade"],
            nivel=definicao["nivel"],
            duracao_horas=definicao["duracao_horas"],
            numero_aulas=definicao["numero_aulas"],
            preco=definicao["preco"],
            moeda="AOA",
            instructor_id=formador.id,
            area=definicao["area"],
            estado=CourseStatus.PUBLISHED,
            inscricoes_abertas=True,
            percentagem_conclusao_minima=definicao["percentagem_conclusao_minima"],
            aulas_obrigatorias_minimas=definicao["aulas_obrigatorias_minimas"],
        )
        db.add(curso)
        db.flush()

        for ordem_modulo, (titulo_modulo, descricao_modulo, aulas) in enumerate(
            definicao["modulos"], start=1
        ):
            modulo = CourseModule(
                curso_id=curso.id,
                titulo=titulo_modulo,
                descricao=descricao_modulo,
                ordem=ordem_modulo,
            )
            db.add(modulo)
            db.flush()

            for ordem_aula, (titulo_aula, descricao_aula, tipo, duracao) in enumerate(
                aulas, start=1
            ):
                aula = Lesson(
                    modulo_id=modulo.id,
                    titulo=titulo_aula,
                    descricao=descricao_aula,
                    tipo=tipo,
                    ordem=ordem_aula,
                    duracao_minutos=duracao,
                    obrigatoria=True,
                    conteudo=(
                        "Conteúdo de demonstração. O texto real da aula, o vídeo "
                        "e os materiais de apoio são carregados pela equipa "
                        "formadora através do painel de administração."
                    ),
                )
                db.add(aula)
                db.flush()
                db.add(
                    LessonMaterial(
                        aula_id=aula.id,
                        titulo=f"Apontamentos — {titulo_aula}",
                        descricao="Material de apoio da aula.",
                        tipo="FICHEIRO",
                        url=None,
                    )
                )

        avaliacao_def = definicao.get("avaliacao")
        if avaliacao_def:
            avaliacao = Assessment(
                course_id=curso.id,
                titulo=avaliacao_def["titulo"],
                descricao=avaliacao_def["descricao"],
                tipo=AssessmentType.TESTE,
                nota_maxima=100,
                nota_aprovacao=50,
                tentativas_maximas=3,
                published=True,
            )
            db.add(avaliacao)
            db.flush()
            for ordem, (enunciado, opcoes, correcta) in enumerate(
                avaliacao_def["perguntas"], start=1
            ):
                db.add(
                    Question(
                        assessment_id=avaliacao.id,
                        enunciado=enunciado,
                        tipo="OPCAO_MULTIPLA",
                        opcoes=json.dumps(opcoes, ensure_ascii=False),
                        resposta_correta=correcta,
                        pontos=1,
                        ordem=ordem,
                    )
                )

        db.add(
            Cohort(
                curso_id=curso.id,
                nome=f"Turma {date.today().year} — {definicao['area']}",
                instructor_id=formador.id,
                data_inicio=date.today() + timedelta(days=14),
                vagas=30,
                estado="ATIVA",
            )
        )
        db.flush()
        print(f"[+] Curso criado: {curso.nome}")


ARTIGOS_DEMO = [
    {
        "titulo": "Como a CLOP Academy estrutura a formação em mercados",
        "resumo": (
            "Explicamos a metodologia usada para converter conceitos "
            "financeiros em aulas práticas e avaliadas."
        ),
        "conteudo": (
            "Este artigo é conteúdo de demonstração da plataforma. A CLOP "
            "Academia Digital, LDA. organiza a sua formação em três pilares: "
            "conceito, prática e avaliação.\n\n"
            "Cada módulo começa por uma aula conceptual e termina com um "
            "exercício avaliado, garantindo que o aluno consolida o "
            "aprendizagem antes de avançar.\n\n"
            "O conteúdo real é publicado pela equipa editorial através do "
            "painel de administração."
        ),
        "tipo": ArticleType.EDUCATIVO,
        "categoria": "Educação Financeira",
        "autor_nome": "Equipa Editorial CLOP",
    },
    {
        "titulo": "Entenda a lógica por trás do nosso portal de mercados",
        "resumo": (
            "Porque distinguimos sempre tempo real, atrasado e histórico — e "
            "porque nunca apresentamos valores sem fonte."
        ),
        "conteudo": (
            "Este artigo é conteúdo de demonstração da plataforma.\n\n"
            "No portal de mercados da CLOP Academy cada valor apresentado "
            "identifica a sua fonte, a data a que respeita e o momento em que "
            "foi consultado. Quando uma integração ainda não está configurada, "
            "a plataforma informa o utilizador em vez de mostrar números "
            "sem origem.\n\n"
            "Este é um compromisso editorial: informação financeira sem "
            "proveniência não é informação, é ruído."
        ),
        "tipo": ArticleType.ANALISE,
        "categoria": "Mercados Financeiros",
        "autor_nome": "Equipa Editorial CLOP",
    },
    {
        "titulo": "Guia de boas práticas: usar a IA no trabalho quotidiano",
        "resumo": (
            "Checklist prática para quem começou a usar assistentes de IA na "
            "rotina de trabalho."
        ),
        "conteudo": (
            "Este artigo é conteúdo de demonstração da plataforma.\n\n"
            "Comece por tarefas repetitivas e de baixo risco, verifique sempre "
            "os resultados e nunca partilhe informação sensível sem "
            "autorização.\n\n"
            "A formação da CLOP inclui um módulo dedicated à utilização "
            "responsável de inteligência artificial."
        ),
        "tipo": ArticleType.EDUCATIVO,
        "categoria": "Tecnologia e IA",
        "autor_nome": "Equipa Editorial CLOP",
    },
]


def garantir_artigos(db: Session, categorias: dict[str, Category]) -> None:
    for definicao in ARTIGOS_DEMO:
        slug = slugify(definicao["titulo"])
        if db.query(Article).filter(Article.slug == slug).first():
            print(f"[=] Artigo já existe: {definicao['titulo']}")
            continue

        categoria = categorias.get(definicao["categoria"])
        artigo = Article(
            titulo=definicao["titulo"],
            slug=slug,
            resumo=definicao["resumo"],
            conteudo=definicao["conteudo"],
            tipo=definicao["tipo"],
            estado=ArticleStatus.PUBLICADO,
            categoria_id=categoria.id if categoria else None,
            autor_nome=definicao["autor_nome"],
            publicado_em=_agora(),
            tags="demonstração, CLOP Academy",
        )
        db.add(artigo)
        db.flush()
        print(f"[+] Artigo criado: {artigo.titulo}")


def garantir_eventos(db: Session, categorias: dict[str, Category]) -> None:
    eventos = [
        {
            "titulo": "Sessão aberta — Planeamento financeiro para jovens",
            "resumo": (
                "Encontro gratuito de apresentação do programa de educação "
                "financeira para estudantes e profissionais jovens."
            ),
            "descricao": (
                "Sessão de demonstração com apresentação do programa de "
                "educação financeira, casos práticos e espaço para perguntas. "
                "A inscrição é gratuita e a capacidade limitada."
            ),
            "categoria": "Educação Financeira",
            "formato": "PRESENCIAL",
            "vagas": 40,
            "dias": 21,
        },
        {
            "titulo": "Webinar — Leitura de índices e taxas de juro",
            "resumo": (
                "Webinar técnico sobre o funcionamento dos mercados e o "
                "impacto das taxas de juro."
            ),
            "descricao": (
                "Webinar de demonstração conduzido pela equipa de formação "
                "da CLOP, com exemplos práticos e tempo para discussão."
            ),
            "categoria": "Mercados Financeiros",
            "formato": "ONLINE",
            "vagas": 100,
            "dias": 35,
        },
    ]

    for definicao in eventos:
        slug = slugify(definicao["titulo"])
        if db.query(Event).filter(Event.slug == slug).first():
            print(f"[=] Evento já existe: {definicao['titulo']}")
            continue

        inicio = _agora() + timedelta(days=definicao["dias"], hours=3)
        categoria = categorias.get(definicao["categoria"])
        evento = Event(
            titulo=definicao["titulo"],
            slug=slug,
            resumo=definicao["resumo"],
            descricao=definicao["descricao"],
            inicio=inicio,
            fim=inicio + timedelta(hours=3),
            formato=definicao["formato"],
            vagas=definicao["vagas"],
            inscricoes_abertas=True,
            requer_inscricao=True,
            categoria_id=categoria.id if categoria else None,
            estado=EventStatus.PUBLICADO,
            cidade="Luanda" if definicao["formato"] == "PRESENCIAL" else None,
            local=(
                "Luanda, Angola"
                if definicao["formato"] == "PRESENCIAL"
                else None
            ),
        )
        db.add(evento)
        db.flush()
        print(f"[+] Evento criado: {evento.titulo}")


def garantir_projectos(db: Session) -> None:
    projectos = [
        {
            "nome": "CLOP Educa — literacia financeira nas escolas",
            "resumo": (
                "Programa de educação financeira para estudantes do ensino "
                "secundário."
            ),
            "descricao": (
                "Iniciativa institucional da CLOP Academia Digital, LDA. para "
                "levar literacia financeira às escolas, com sessões "
                "presenciais e material pedagógico. Estado e calendarização "
                "são actualizados pela equipa."
            ),
            "area": "Educação Financeira",
            "estado": ProjectStatus.EM_CURSO,
        },
        {
            "nome": "CLOP Estágio — primeira experiência profissional",
            "resumo": "Programa de estágio e orientação para jovens.",
            "descricao": (
                "Programa de estágio que liga estudantes e recém-formados a "
                "organizações, com plano de desenvolvimento de carreira e "
                "acompanhamento."
            ),
            "area": "Formação Profissional",
            "estado": ProjectStatus.EM_CURSO,
        },
        {
            "nome": "CLOP Digital — benchmarking de mercados angolanos",
            "resumo": (
                "Estudo periódico sobre a evolução dos mercados financeiros "
                "em Angola."
            ),
            "descricao": (
                "Iniciativa de observação e publicação sobre o mercado "
                "angolano, baseada exclusivamente em dados com origem "
                "identificada."
            ),
            "area": "Mercados Financeiros",
            "estado": ProjectStatus.PLANEADO,
        },
    ]

    for definicao in projectos:
        slug = slugify(definicao["nome"])
        if db.query(Project).filter(Project.slug == slug).first():
            print(f"[=] Projecto já existe: {definicao['nome']}")
            continue
        projecto = Project(
            nome=definicao["nome"],
            slug=slug,
            resumo=definicao["resumo"],
            descricao=definicao["descricao"],
            area=definicao["area"],
            estado=definicao["estado"],
        )
        db.add(projecto)
        db.flush()
        print(f"[+] Projecto criado: {projecto.nome}")


def garantir_campanha(db: Session) -> None:
    slug = "inscricoes-abertas-formacao-2026"
    if db.query(Campaign).filter(Campaign.slug == slug).first():
        print("[=] Campanha já existe.")
        return

    campanha = Campaign(
        nome="Inscrições abertas — Formação 2026",
        slug=slug,
        descricao=(
            "Estão abertas as inscrições para os cursos de educação financeira, "
            "mercados e transformação digital da CLOP Academy."
        ),
        objetivo="Divulgação de cursos",
        estado=CampaignStatus.EM_CURSO,
        data_inicio=_agora() - timedelta(days=7),
        data_fim=_agora() + timedelta(days=90),
        destaque_home=True,
        link_destino="/formacao",
        texto_botao="Ver cursos",
    )
    db.add(campanha)
    db.flush()
    print(f"[+] Campanha criada: {campanha.nome}")


def main() -> int:
    incluir_demo = "--sem-demo" not in sys.argv

    db = SessionLocal()
    try:
        garantir_admin(db)
        db.commit()

        if incluir_demo:
            categorias = garantir_categorias(db)
            db.commit()
            formador = garantir_formador(db)
            db.commit()
            garantir_cursos(db, formador, categorias)
            garantir_artigos(db, categorias)
            garantir_eventos(db, categorias)
            garantir_projectos(db)
            garantir_campanha(db)
            db.commit()

        print("\n[OK] Populamento inicial concluído.")
        return 0
    except Exception as exc:  # pragma: no cover - utilitário de linha de comando
        db.rollback()
        print(f"[ERRO] {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
