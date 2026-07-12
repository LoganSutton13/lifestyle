import type { FormEventHandler, HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

type DangerZoneBaseProps = {
  title?: string
  children: ReactNode
  className?: string
}

type DangerZoneSectionProps = DangerZoneBaseProps &
  Omit<HTMLAttributes<HTMLElement>, 'children' | 'className'> & {
    as?: 'section'
    onSubmit?: never
  }

type DangerZoneFormProps = DangerZoneBaseProps &
  Omit<HTMLAttributes<HTMLFormElement>, 'children' | 'className' | 'onSubmit'> & {
    as: 'form'
    onSubmit?: FormEventHandler<HTMLFormElement>
  }

export type DangerZoneProps = DangerZoneSectionProps | DangerZoneFormProps

export function DangerZone(props: DangerZoneProps) {
  const { as = 'section', title, className, children, ...rest } = props
  const shellClassName = cn(
    'space-y-4 rounded-2xl border border-danger/30 bg-danger/5 p-4',
    className,
  )

  const body = (
    <>
      {title ? <h2 className="text-lg font-semibold text-danger">{title}</h2> : null}
      {children}
    </>
  )

  if (as === 'form') {
    const { onSubmit, ...formRest } = rest as DangerZoneFormProps
    return (
      <form className={shellClassName} onSubmit={onSubmit} {...formRest}>
        {body}
      </form>
    )
  }

  return (
    <section className={shellClassName} {...(rest as DangerZoneSectionProps)}>
      {body}
    </section>
  )
}
