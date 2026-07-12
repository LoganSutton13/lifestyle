import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, MoreVertical, Trash2 } from 'lucide-react'
import { cn } from '../../lib/cn'
import { trackingTypeLabel } from '../exercises/types'
import type { SessionExercise } from './types'

export interface ExerciseHeaderProps {
  sessionExercise: SessionExercise
  canMoveLeft: boolean
  canMoveRight: boolean
  readOnly?: boolean
  onMoveLeft: () => void
  onMoveRight: () => void
  onRemove: () => void
  onToggleUnilateral: (value: boolean) => void
}

export function ExerciseHeader({
  sessionExercise,
  canMoveLeft,
  canMoveRight,
  readOnly,
  onMoveLeft,
  onMoveRight,
  onRemove,
  onToggleUnilateral,
}: ExerciseHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [menuOpen])

  const { exercise } = sessionExercise

  return (
    <div className="flex items-start justify-between gap-3">
      <div>
        <h2 className="text-xl font-bold text-text">{exercise.name}</h2>
        <p className="text-sm text-textMuted">
          {exercise.equipment.displayName} &middot; {trackingTypeLabel(exercise.trackingType)}
        </p>
      </div>

      <div className="flex items-center gap-2">
        {sessionExercise.exercise.trackingType !== 'duration' ? (
          <label className="flex items-center gap-2 text-xs font-medium text-textMuted">
            <span>Per side</span>
            <input
              type="checkbox"
              checked={sessionExercise.isUnilateral}
              disabled={readOnly}
              onChange={(event) => onToggleUnilateral(event.target.checked)}
              className="h-5 w-5 accent-primary"
              aria-label="Unilateral (per side)"
            />
          </label>
        ) : null}

        {!readOnly ? (
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              aria-label="Exercise options"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
              className="flex min-h-touch min-w-touch items-center justify-center rounded-full text-textMuted hover:bg-surface"
            >
              <MoreVertical className="h-5 w-5" />
            </button>

            {menuOpen ? (
              <div className="absolute right-0 top-full z-20 mt-1 w-48 rounded-xl border border-border bg-surfaceElevated py-1 shadow-lg">
                <button
                  type="button"
                  disabled={!canMoveLeft}
                  onClick={() => {
                    setMenuOpen(false)
                    onMoveLeft()
                  }}
                  className={cn(
                    'flex w-full min-h-touch items-center gap-2 px-3 text-sm text-text hover:bg-surface',
                    !canMoveLeft && 'cursor-not-allowed opacity-40',
                  )}
                >
                  <ArrowLeft className="h-4 w-4" /> Move left
                </button>
                <button
                  type="button"
                  disabled={!canMoveRight}
                  onClick={() => {
                    setMenuOpen(false)
                    onMoveRight()
                  }}
                  className={cn(
                    'flex w-full min-h-touch items-center gap-2 px-3 text-sm text-text hover:bg-surface',
                    !canMoveRight && 'cursor-not-allowed opacity-40',
                  )}
                >
                  <ArrowRight className="h-4 w-4" /> Move right
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false)
                    onRemove()
                  }}
                  className="flex w-full min-h-touch items-center gap-2 px-3 text-sm text-danger hover:bg-danger/10"
                >
                  <Trash2 className="h-4 w-4" /> Remove exercise
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}
