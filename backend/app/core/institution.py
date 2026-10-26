"""Configuração central da identidade institucional da CLOP.

Todos os contactos, textos institucionais e áreas de actuação residem aqui.
Para alterar a identidade da instituição basta editar as variáveis de
ambiente definidas em `INSTITUTION_*` (ver `.env.example`) — nenhum outro
ficheiro do projecto precisa de ser tocado.
"""

from dataclasses import dataclass, field

from app.core.config import settings

ASSINATURA = (
    "Educação Financeira & Mercados — Conhecimento que transforma "
    "oportunidades em resultados."
)

VALORES = (
    "Integridade e responsabilidade",
    "Excelência",
    "Inovação",
    "Educação e conhecimento",
    "Inclusão e igualdade de oportunidades",
    "Empreendedorismo",
    "Compromisso social",
    "Colaboração",
)

AREAS_ACTUACAO = (
    {
        "id": "educacao-financeira",
        "titulo": "Educação Financeira e Investimentos",
        "descricao": (
            "Literacia financeira, planeamento de poupança, orçamento pessoal, "
            "instrumentos de investimento e leitura de mercados."
        ),
    },
    {
        "id": "formacao-profissional",
        "titulo": "Formação Profissional, Estágio e Plano de Carreira",
        "descricao": (
            "Capacitação técnica, orientação profissional, estágio e "
            "planos de desenvolvimento de carreira."
        ),
    },
    {
        "id": "inteligencia-artificial",
        "titulo": "Inteligência Artificial e Transformação Digital",
        "descricao": (
            "Alfabetização em IA, automatização de processos, análise de dados "
            "e digitalização de pequenos negócios."
        ),
    },
    {
        "id": "empreendedorismo",
        "titulo": "Empreendedorismo e Criação de Rendimento",
        "descricao": (
            "Construção de negócios, modelos de receita, acesso a mercados "
            "e apoio ao empreendedorismo jovem."
        ),
    },
    {
        "id": "desenvolvimento-pessoal",
        "titulo": "Desenvolvimento Pessoal e Liderança",
        "descricao": (
            "Comunicação, gestão do tempo, trabalho em equipa, liderança "
            "e construção de hábitos profissionais."
        ),
    },
    {
        "id": "comunicacao-digital",
        "titulo": "Comunicação, Educação e Produção Digital",
        "descricao": (
            "Produção de conteúdos, comunicação institucional, marketing "
            "digital e produção audiovisual."
        ),
    },
)


def _parse_social_links(raw: str) -> dict[str, str]:
    """Converte "Facebook=https://...,LinkedIn=https://..." num dicionário.

    Redes não configuradas são simplesmente omitidas — a interface nunca
    apresenta ligações de redes sociais inventadas.
    """
    links: dict[str, str] = {}
    for part in raw.split(","):
        name, separator, url = part.partition("=")
        if not separator:
            continue
        name = name.strip()
        url = url.strip()
        if name and url:
            links[name] = url
    return links


@dataclass(frozen=True)
class Institution:
    nome: str = settings.INSTITUTION_NAME
    area: str = settings.INSTITUTION_AREA
    assinatura: str = ASSINATURA
    slogan: str = "Conhecimento que transforma oportunidades em resultados."
    missao: str = (
        "Promover a educação, a literacia financeira, o desenvolvimento de "
        "competências e a empregabilidade, através de programas de formação, "
        "estágio, orientação profissional e inovação digital."
    )
    visao: str = (
        "Ser uma instituição de referência em Angola e, progressivamente, no "
        "espaço africano, nas áreas da educação financeira, formação "
        "profissional, desenvolvimento juvenil e inovação digital."
    )
    valores: tuple[str, ...] = VALORES
    areas_actuacao: tuple[dict, ...] = AREAS_ACTUACAO
    morada: str = settings.INSTITUTION_ADDRESS
    unitel: str = settings.INSTITUTION_UNITEL
    africell: str = settings.INSTITUTION_AFRICELL
    email: str = settings.INSTITUTION_EMAIL
    cidade: str = "Luanda"
    pais: str = "Angola"
    social: dict[str, str] = field(
        default_factory=lambda: _parse_social_links(settings.INSTITUTION_SOCIAL_LINKS)
    )

    def contactos(self) -> dict[str, str]:
        return {
            "morada": self.morada,
            "unitel": self.unitel,
            "africell": self.africell,
            "email": self.email,
        }


institution = Institution()
