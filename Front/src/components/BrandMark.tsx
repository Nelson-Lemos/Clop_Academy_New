import type { CSSProperties } from 'react'

type BrandMarkProps = {
  theme?: 'light' | 'dark'
  href?: string
  className?: string
  emblemSize?: number
}

/**
 * Assinatura visual CLOP: emblema (touro + torres) + lockup tipográfico.
 * O emblema deriva directamente da marca original em /public/brand.
 */
export function BrandMark({
  theme = 'light',
  href = '#inicio',
  className = '',
  emblemSize = 46,
}: BrandMarkProps) {
  return (
    <a
      className={`clop-brand clop-brand--${theme} ${className}`.trim()}
      href={href}
      aria-label="CLOP Academia Digital — início"
      style={{ '--brand-emblem-size': `${emblemSize}px` } as CSSProperties}
    >
      <img
        className="clop-brand__emblem"
        src="/brand/clop-emblem.png"
        alt=""
        width={emblemSize}
        height={emblemSize}
        decoding="async"
      />
      <span className="clop-brand__text">
        <strong>CLOP</strong>
        <span>Academia Digital</span>
      </span>
    </a>
  )
}
