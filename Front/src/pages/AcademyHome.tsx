import { useState, type FormEvent } from 'react'
import {
  ArrowDown,
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  Check,
  GraduationCap,
  Landmark,
  Mail,
  Menu,
  MonitorCog,
  Scale,
  UsersRound,
  X,
} from 'lucide-react'
import { BrandMark } from '../components/BrandMark'
import { institution } from '../config/institution'
import { useAuth } from '../contexts/AuthContext'
import '../styles/academy.css'

const focusAreas = [
  {
    icon: Landmark,
    title: 'Educação financeira e investimentos',
    description: 'Compreender conceitos financeiros e os mercados com responsabilidade.',
  },
  {
    icon: GraduationCap,
    title: 'Formação profissional e carreira',
    description: 'Desenvolver competências, orientação profissional e empregabilidade.',
  },
  {
    icon: MonitorCog,
    title: 'Inteligência artificial e transformação digital',
    description: 'Explorar competências digitais úteis para um mundo em mudança.',
  },
  {
    icon: BriefcaseBusiness,
    title: 'Empreendedorismo e criação de rendimento',
    description: 'Promover iniciativa, conhecimento e soluções sustentáveis.',
  },
  {
    icon: UsersRound,
    title: 'Desenvolvimento pessoal e liderança',
    description: 'Apoiar o crescimento pessoal, a colaboração e a liderança responsável.',
  },
  {
    icon: BookOpen,
    title: 'Comunicação e produção digital',
    description: 'Capacitar para comunicar e criar conteúdos no ambiente digital.',
  },
]

const initiatives = [
  'Programa CLOP para Empregabilidade',
  'Educação Financeira para Jovens',
  'Núcleos de Educação Financeira e Investidores',
  'Formação em Inteligência Artificial e Competências Digitais',
  'Programas de Estágio e Orientação Profissional',
  'Expansão de Parcerias Institucionais',
]

const navigation = [
  ['Sobre', '#sobre'],
  ['Formação', '#formacao'],
  ['Mercados', '#mercados'],
  ['Actualidade', '#actualidade'],
  ['Iniciativas', '#iniciativas'],
  ['Contactos', '#contactos'],
] as const

const credoWords = [
  'Análise',
  'Estratégia',
  'Resultados',
  'Confiança',
  'Disciplina',
  'Lucro',
]

function openEmail(subject: string, body: string) {
  const mailto = `mailto:${institution.contacts.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  window.location.href = mailto
}

export default function AcademyHome({ onLogout }: { onLogout?: () => void } = {}) {
  const { isAuthenticated, user, logout } = useAuth()

  const handleLogout = () => {
    onLogout?.()
    logout()
  }
  const [menuOpen, setMenuOpen] = useState(false)

  function submitPartnership(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const body = [
      `Nome: ${values.get('name')}`,
      `Instituição: ${values.get('organization') || 'Não indicada'}`,
      `E-mail: ${values.get('email')}`,
      `Área de colaboração: ${values.get('area')}`,
      '',
      'Proposta:',
      values.get('message'),
    ].join('\n')

    openEmail('Proposta de colaboração institucional', body)
  }

  function submitNewsletter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    openEmail(
      'Pedido de subscrição da newsletter',
      `Solicito receber actualizações institucionais da CLOP Academia Digital neste endereço: ${values.get('email')}\n\nConsinto o envio de actualizações por e-mail. Sei que este pedido só será enviado quando confirmar o envio no meu cliente de e-mail.`,
    )
  }

  return (
    <div className="academy">
      <header className="academy-header">
        <BrandMark theme="light" href="#inicio" emblemSize={46} />
        <button
          className="academy-menu-toggle"
          type="button"
          aria-label={menuOpen ? 'Fechar navegação' : 'Abrir navegação'}
          aria-expanded={menuOpen}
          aria-controls="academy-navigation"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
        <nav
          id="academy-navigation"
          className={`academy-navigation${menuOpen ? ' is-open' : ''}`}
          aria-label="Navegação principal"
        >
          {navigation.map(([label, href]) => (
            <a key={href} href={href} onClick={() => setMenuOpen(false)}>
              {label}
            </a>
          ))}
          <span className="academy-header-divider" aria-hidden="true" />
          {isAuthenticated ? (
            <div className="academia-header-usuario">
              <span className="academy-usuario-nome">{user?.nome_completo || user?.email}</span>
              <button className="academy-header-sair" onClick={handleLogout}>
                Sair
              </button>
            </div>
          ) : (
            <>
              <a className="academy-header-login" href="#/entrar">
                Entrar
              </a>
              <a className="academy-header-cta" href="#/registar">
                Criar conta <ArrowRight size={15} aria-hidden="true" />
              </a>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="academy-hero" id="inicio">
          <div className="academy-hero__backdrop" aria-hidden="true">
            <span className="academy-hero__glow" />
            <span className="academy-hero__grid" />
          </div>

          <div className="academy-hero__inner">
            <div className="academy-hero__content">
              <p className="academy-eyebrow">
                <span aria-hidden="true" />
                CLOP Academia Digital · Luanda
              </p>
              <h1>
                Conhecimento que transforma <em>oportunidades</em> em resultados.
              </h1>
              <p className="academy-hero__copy">
                A CLOP Academia Digital promove a educação financeira, a formação profissional e
                o desenvolvimento de competências para criar novas oportunidades em Angola.
              </p>

              <div className="academy-hero__actions">
                <a className="academy-button academy-button--primary" href="#/registar">
                  Criar a minha conta <ArrowRight size={17} aria-hidden="true" />
                </a>
                <a className="academy-button academy-button--ghost" href="#/entrar">
                  Já tenho conta
                </a>
              </div>

              <ul className="academy-hero__pillars" aria-label="Princípios CLOP">
                {institution.pillars.map((pillar) => (
                  <li key={pillar}>{pillar}</li>
                ))}
              </ul>

              <a className="academy-hero__scroll" href="#sobre">
                Conhecer a instituição <ArrowDown size={15} aria-hidden="true" />
              </a>
            </div>

            <div className="academy-hero__art" aria-hidden="true">
              <span className="academy-hero__halo" />
              <span className="academy-hero__orbit academy-hero__orbit--outer" />
              <span className="academy-hero__orbit academy-hero__orbit--inner" />
              <img
                className="academy-hero__watermark"
                src="/brand/clop-emblem.png"
                alt=""
                decoding="async"
              />

              <div className="academy-hero__frame">
                <video
                  className="academy-hero__film"
                  src="/brand/clop-brand-film.mp4"
                  poster="/brand/clop-brand-poster.jpg"
                  autoPlay
                  muted
                  loop
                  playsInline
                  preload="metadata"
                />
                <span className="academy-hero__frame-grain" />
                <div className="academy-hero__frame-meta">
                  <span>CLOP · brand film</span>
                  <span>00:08</span>
                </div>
              </div>

              <span className="academy-hero__tag academy-hero__tag--a">Análise</span>
              <span className="academy-hero__tag academy-hero__tag--b">Estratégia</span>
              <span className="academy-hero__tag academy-hero__tag--c">Resultados</span>
            </div>
          </div>

          <div className="academy-hero__foot">
            <span>Kinaxixi · Luanda, Angola</span>
            <span className="academy-hero__foot-center">Educação financeira &amp; mercados</span>
            <span>Confiança · Disciplina · Lucro</span>
          </div>
        </section>

        <div className="academy-credo" aria-hidden="true">
          <div className="academy-credo__track">
            {[0, 1].map((group) => (
              <div className="academy-credo__group" key={group}>
                {[...credoWords, ...credoWords].map((word, index) => (
                  <span className="academy-credo__word" key={`${group}-${index}-${word}`}>
                    {word}
                    <i>◆</i>
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>

        <section className="academy-section academy-intro" id="sobre">
          <div className="academy-section-heading">
            <p className="academy-eyebrow">
              <span aria-hidden="true" />
              Quem somos
            </p>
            <h2>Conhecimento para transformar oportunidades em resultados.</h2>
          </div>
          <div className="academy-intro-copy">
            <p>
              A {institution.name} é uma instituição orientada para a educação financeira,
              formação profissional, desenvolvimento pessoal, inteligência artificial,
              transformação digital e empreendedorismo.
            </p>
            <p>
              Trabalhamos para ampliar o acesso ao conhecimento, apoiar a capacitação e contribuir
              para a empregabilidade e a inovação digital em Angola.
            </p>
          </div>
          <div className="academy-purpose-grid">
            <article>
              <span className="academy-index">01 / MISSÃO</span>
              <h3>Capacitar para avançar</h3>
              <p>
                Promover a educação, a literacia financeira, o desenvolvimento de competências e a
                empregabilidade através de formação, orientação e inovação.
              </p>
            </article>
            <article>
              <span className="academy-index">02 / VISÃO</span>
              <h3>Construir referência</h3>
              <p>
                Ser uma instituição de referência em Angola e, progressivamente, no espaço
                africano, nas áreas da educação financeira, formação juvenil e inovação digital.
              </p>
            </article>
            <article>
              <span className="academy-index">03 / VALORES</span>
              <h3>Agir com responsabilidade</h3>
              <p>
                Integridade, responsabilidade, excelência, inovação, inclusão, educação,
                empreendedorismo, compromisso social e colaboração.
              </p>
            </article>
          </div>
        </section>

        <section className="academy-section academy-focus" id="areas">
          <div className="academy-section-heading">
            <p className="academy-eyebrow">
              <span aria-hidden="true" />
              Áreas de actuação
            </p>
            <h2>Competências para a vida e para o trabalho.</h2>
            <p className="academy-section-lead">
              Uma abordagem que liga conhecimento, desenvolvimento profissional e inovação.
            </p>
          </div>
          <div className="academy-focus-grid">
            {focusAreas.map(({ icon: Icon, title, description }, index) => (
              <article className="academy-focus-card" key={title}>
                <div className="academy-focus-card-top">
                  <Icon size={22} strokeWidth={1.7} aria-hidden="true" />
                  <span>0{index + 1}</span>
                </div>
                <h3>{title}</h3>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="academy-section academy-training" id="formacao">
          <div className="academy-section-heading">
            <p className="academy-eyebrow">
              <span aria-hidden="true" />
              Formação
            </p>
            <h2>Aprendizagem com propósito.</h2>
          </div>
          <div className="academy-empty-panel">
            <div className="academy-empty-icon">
              <GraduationCap size={24} aria-hidden="true" />
            </div>
            <div className="academy-empty-copy">
              <h3>O catálogo de cursos está em preparação.</h3>
              <p>
                Ainda não existem cursos publicados com programa, calendário, modalidade e
                condições de inscrição confirmados. Crie a sua conta para ser informado das
                próximas formações.
              </p>
            </div>
            <div className="academy-empty-actions">
              <a className="academy-button academy-button--primary" href="#/registar">
                Criar conta <ArrowRight size={16} aria-hidden="true" />
              </a>
              <a
                className="academy-button academy-button--outline"
                href={`mailto:${institution.contacts.email}?subject=${encodeURIComponent('Informações sobre formações')}`}
              >
                Pedir informações
              </a>
            </div>
          </div>
        </section>

        <section className="academy-section academy-markets" id="mercados">
          <div className="academy-market-copy">
            <p className="academy-eyebrow">
              <span aria-hidden="true" />
              Mercados financeiros
            </p>
            <h2>Informação responsável começa por fontes claras.</h2>
            <p>
              Esta área foi preparada para conteúdos educativos sobre mercados internacionais e o
              mercado de capitais angolano, incluindo a BODIVA. Não apresentamos cotações enquanto
              não houver uma fonte de dados validada e configurada.
            </p>
            <p className="academy-disclaimer">
              Os conteúdos financeiros têm finalidade informativa e educativa; não constituem
              aconselhamento financeiro personalizado.
            </p>
          </div>
          <div className="academy-market-status">
            <div className="academy-market-status-heading">
              <span className="academy-status-indicator" aria-hidden="true" />
              <span>Estado da informação de mercado</span>
            </div>
            <div className="academy-market-status-content">
              <Scale size={26} strokeWidth={1.5} aria-hidden="true" />
              <div>
                <strong>Dados de mercado indisponíveis</strong>
                <p>
                  Nenhum fornecedor de cotações está configurado. Não são apresentados preços,
                  variações ou dados em tempo real.
                </p>
              </div>
            </div>
            <div className="academy-market-status-footer">
              <span>Fonte</span>
              <span>Sem integração activa</span>
            </div>
          </div>
        </section>

        <section className="academy-section academy-editorial" id="actualidade">
          <div className="academy-section-heading">
            <p className="academy-eyebrow">
              <span aria-hidden="true" />
              Notícias, análises e actividades
            </p>
            <h2>Conhecimento partilhado com rigor.</h2>
          </div>
          <div className="academy-editorial-grid">
            <article>
              <span className="academy-editorial-label">Publicações</span>
              <h3>Sem artigos publicados</h3>
              <p>
                Notícias, análises e conteúdos educativos serão apresentados quando forem
                publicados e identificados com a respectiva natureza e fonte.
              </p>
            </article>
            <article>
              <span className="academy-editorial-label">Actividades</span>
              <h3>Sem eventos anunciados</h3>
              <p>
                Ainda não há eventos ou actividades com data e condições de participação
                confirmadas.
              </p>
            </article>
          </div>
        </section>

        <section className="academy-section academy-initiatives" id="iniciativas">
          <div className="academy-section-heading">
            <p className="academy-eyebrow">
              <span aria-hidden="true" />
              Projectos e iniciativas
            </p>
            <h2>Ideias com potencial para gerar impacto.</h2>
            <p className="academy-section-lead">
              As iniciativas abaixo são linhas de trabalho propostas; não são apresentadas como
              programas já executados.
            </p>
          </div>
          <ul className="academy-initiative-list">
            {initiatives.map((initiative) => (
              <li key={initiative}>
                <span className="academy-initiative-icon">
                  <Check size={15} aria-hidden="true" />
                </span>
                <span>{initiative}</span>
                <span className="academy-planned-label">Planeada</span>
              </li>
            ))}
          </ul>
          <div className="academy-initiatives-cta">
            <p>Acompanhe o desenvolvimento destas iniciativas a partir da sua área de aluno.</p>
            <a className="academy-text-link" href="#/entrar">
              Entrar na Academia <ArrowRight size={16} aria-hidden="true" />
            </a>
          </div>
        </section>

        <section className="academy-section academy-partners" id="parcerias">
          <div className="academy-partner-copy">
            <p className="academy-eyebrow">
              <span aria-hidden="true" />
              Parcerias
            </p>
            <h2>Vamos criar oportunidades em conjunto.</h2>
            <p>
              A CLOP está aberta a propostas de colaboração alinhadas com a educação, a
              empregabilidade, a literacia financeira e a inovação em Angola.
            </p>
          </div>
          <form className="academy-partner-form" onSubmit={submitPartnership}>
            <label>
              Nome
              <input name="name" autoComplete="name" required />
            </label>
            <label>
              E-mail
              <input name="email" type="email" autoComplete="email" required />
            </label>
            <label>
              Instituição (opcional)
              <input name="organization" autoComplete="organization" />
            </label>
            <label>
              Área da proposta
              <select name="area" required defaultValue="">
                <option value="" disabled>
                  Seleccione uma área
                </option>
                <option>Educação e formação</option>
                <option>Empregabilidade e estágio</option>
                <option>Educação financeira</option>
                <option>Tecnologia e inovação</option>
                <option>Outra proposta</option>
              </select>
            </label>
            <label className="academy-form-wide">
              Mensagem
              <textarea name="message" rows={4} required />
            </label>
            <p className="academy-form-note academy-form-wide">
              Ao continuar, será aberto o seu cliente de e-mail com a proposta preenchida. O portal
              não guarda nem envia automaticamente os dados deste formulário.
            </p>
            <button
              className="academy-button academy-button--primary academy-form-wide"
              type="submit"
            >
              Preparar proposta <ArrowRight size={16} aria-hidden="true" />
            </button>
          </form>
        </section>

        <section className="academy-newsletter" id="actualizacoes">
          <div>
            <p className="academy-eyebrow">
              <span aria-hidden="true" />
              Actualizações CLOP
            </p>
            <h2>Receba novidades institucionais.</h2>
            <p>O pedido só será enviado depois de confirmar o envio no seu cliente de e-mail.</p>
          </div>
          <form className="academy-newsletter-form" onSubmit={submitNewsletter}>
            <label className="academy-sr-only" htmlFor="newsletter-email">
              O seu endereço de e-mail
            </label>
            <div className="academy-newsletter-controls">
              <input
                id="newsletter-email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="O seu endereço de e-mail"
                required
              />
              <button className="academy-button academy-button--dark" type="submit">
                Pedir subscrição <Mail size={16} aria-hidden="true" />
              </button>
            </div>
            <label className="academy-consent">
              <input name="consent" type="checkbox" required />
              <span>Consinto o envio de actualizações institucionais para o endereço indicado.</span>
            </label>
          </form>
        </section>
      </main>

      <footer className="academy-footer" id="contactos">
        <div className="academy-footer-main">
          <div className="academy-footer-brand">
            <BrandMark theme="light" href="#inicio" emblemSize={54} />
            <p>{institution.signature}</p>
            <p className="academy-footer-credo">Análise · Estratégia · Resultados</p>
          </div>
          <div className="academy-footer-column">
            <h2>Explorar</h2>
            <a href="#sobre">Sobre a CLOP</a>
            <a href="#formacao">Formação</a>
            <a href="#mercados">Mercados</a>
            <a href="#actualidade">Actualidade</a>
            <a href="#iniciativas">Iniciativas</a>
          </div>
          <div className="academy-footer-column academy-footer-contact">
            <h2>Contactos</h2>
            <p>{institution.contacts.location}</p>
            {institution.contacts.phones.map((phone) => (
              <a key={phone.label} href={`tel:${phone.link}`}>
                {phone.label}: {phone.number}
              </a>
            ))}
            <a href={`mailto:${institution.contacts.email}`}>{institution.contacts.email}</a>
          </div>
          <div className="academy-footer-column">
            <h2>Informação</h2>
            <a href="#/entrar">Área de aluno</a>
            <a href="#/registar">Criar conta</a>
            <a href="#privacidade">Privacidade</a>
            <a href="#termos">Termos e avisos</a>
            <a href={`mailto:${institution.contacts.email}`}>Fale connosco</a>
          </div>
        </div>
        <div className="academy-footer-bottom">
          <span>
            © {new Date().getFullYear()} {institution.name}
          </span>
          <span>Luanda, Angola</span>
          <span className="academy-footer-bottom-credo">Confiança · Disciplina · Lucro</span>
        </div>
        <div className="academy-legal" id="privacidade">
          <p>
            <strong>Privacidade:</strong> os formulários desta página abrem uma mensagem no cliente
            de e-mail do visitante. O portal não armazena os dados submetidos por esses
            formulários.
          </p>
          <p id="termos">
            <strong>Termos e avisos:</strong> os conteúdos são informativos e educativos. Não
            constituem aconselhamento financeiro personalizado nem uma oferta de investimento.
          </p>
        </div>
      </footer>
    </div>
  )
}
