import { useCallback, useEffect, useRef, useState } from 'react'
import { Minus, Pause, Play, Plus, RotateCcw } from 'lucide-react'
import { cn } from '../../lib/cn'
import { useToast } from '../../components/ui/Toast'

interface RestTimerState {
  durationSeconds: number
  endsAt: number | null
  pausedRemainingSeconds: number
}

export interface RestTimerProps {
  sessionId: string
  defaultDurationSeconds: number
  className?: string
}

function storageKey(sessionId: string): string {
  return `rest-timer:${sessionId}`
}

function loadState(sessionId: string, fallbackDuration: number): RestTimerState {
  try {
    const raw = window.sessionStorage.getItem(storageKey(sessionId))
    if (raw) {
      return JSON.parse(raw) as RestTimerState
    }
  } catch {
    // ignore malformed storage
  }
  return { durationSeconds: fallbackDuration, endsAt: null, pausedRemainingSeconds: fallbackDuration }
}

function computeRemaining(state: RestTimerState): number {
  if (state.endsAt !== null) {
    return Math.max(0, Math.ceil((state.endsAt - Date.now()) / 1000))
  }
  return state.pausedRemainingSeconds
}

function formatRemaining(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

export function RestTimer({ sessionId, defaultDurationSeconds, className }: RestTimerProps) {
  const [state, setState] = useState<RestTimerState>(() => loadState(sessionId, defaultDurationSeconds))
  const [, forceTick] = useState(0)
  const hasNotifiedZero = useRef(false)
  const { showToast } = useToast()

  const persist = useCallback(
    (next: RestTimerState) => {
      setState(next)
      try {
        window.sessionStorage.setItem(storageKey(sessionId), JSON.stringify(next))
      } catch {
        // ignore storage failures (e.g. private browsing quota)
      }
    },
    [sessionId],
  )

  useEffect(() => {
    setState(loadState(sessionId, defaultDurationSeconds))
  }, [sessionId, defaultDurationSeconds])

  useEffect(() => {
    const interval = window.setInterval(() => forceTick((tick) => tick + 1), 1000)
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        forceTick((tick) => tick + 1)
      }
    }
    document.addEventListener('visibilitychange', handleVisibility)
    return () => {
      window.clearInterval(interval)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [])

  const remaining = computeRemaining(state)
  const isRunning = state.endsAt !== null

  useEffect(() => {
    if (isRunning && remaining === 0) {
      if (!hasNotifiedZero.current) {
        hasNotifiedZero.current = true
        showToast('Rest complete', 'success')
        if (typeof navigator !== 'undefined' && navigator.vibrate) {
          navigator.vibrate(200)
        }
      }
      persist({ ...state, endsAt: null, pausedRemainingSeconds: 0 })
    } else if (remaining > 0) {
      hasNotifiedZero.current = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [remaining, isRunning])

  function handleStartPause() {
    if (isRunning) {
      persist({ ...state, endsAt: null, pausedRemainingSeconds: remaining })
    } else {
      const base = remaining > 0 ? remaining : state.durationSeconds
      persist({ ...state, endsAt: Date.now() + base * 1000, pausedRemainingSeconds: 0 })
    }
  }

  function handleReset() {
    persist({ durationSeconds: defaultDurationSeconds, endsAt: null, pausedRemainingSeconds: defaultDurationSeconds })
  }

  function handleAdjust(delta: number) {
    if (isRunning && state.endsAt !== null) {
      const nextRemaining = Math.max(0, remaining + delta)
      persist({ ...state, endsAt: Date.now() + nextRemaining * 1000 })
    } else {
      const nextRemaining = Math.max(0, state.pausedRemainingSeconds + delta)
      persist({ ...state, pausedRemainingSeconds: nextRemaining })
    }
  }

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-2 rounded-2xl border border-border bg-surfaceElevated px-4 py-2.5 shadow-sm',
        className,
      )}
      role="group"
      aria-label="Rest timer"
    >
      <button
        type="button"
        aria-label="Reset rest timer"
        onClick={handleReset}
        className="flex min-h-touch min-w-touch items-center justify-center rounded-full text-textMuted hover:bg-surface"
      >
        <RotateCcw className="h-4 w-4" />
      </button>

      <button
        type="button"
        aria-label="Subtract 15 seconds"
        onClick={() => handleAdjust(-15)}
        className="flex min-h-touch min-w-touch items-center justify-center rounded-full text-textMuted hover:bg-surface"
      >
        <Minus className="h-4 w-4" />
      </button>

      <span
        className={cn('min-w-[4.5rem] text-center text-lg font-semibold tabular-nums', remaining === 0 && isRunning === false && state.pausedRemainingSeconds === 0 ? 'text-success' : 'text-text')}
        aria-live="polite"
      >
        {formatRemaining(remaining)}
      </span>

      <button
        type="button"
        aria-label="Add 15 seconds"
        onClick={() => handleAdjust(15)}
        className="flex min-h-touch min-w-touch items-center justify-center rounded-full text-textMuted hover:bg-surface"
      >
        <Plus className="h-4 w-4" />
      </button>

      <button
        type="button"
        aria-label={isRunning ? 'Pause rest timer' : 'Start rest timer'}
        onClick={handleStartPause}
        className="flex min-h-touch min-w-touch items-center justify-center rounded-full bg-primary text-white hover:bg-primaryDark"
      >
        {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
      </button>
    </div>
  )
}
