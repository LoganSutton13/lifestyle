import { Check } from 'lucide-react'
import { Card } from '../../components/ui/Card'
import { cn } from '../../lib/cn'
import type { ChecklistTask } from './api'

export interface TaskItemProps {
  task: ChecklistTask
  disabled?: boolean
  onToggle: (completed: boolean) => void
}

export function TaskItem({ task, disabled, onToggle }: TaskItemProps) {
  return (
    <Card className="flex items-start gap-3">
      <div className="min-w-0 flex-1">
        <h3 className="font-medium text-text">{task.title}</h3>
        {task.description ? (
          <p className="mt-1 text-sm text-textMuted">{task.description}</p>
        ) : null}
      </div>
      <button
        type="button"
        aria-label={task.completed ? `Mark ${task.title} incomplete` : `Mark ${task.title} complete`}
        aria-pressed={task.completed}
        disabled={disabled}
        onClick={() => onToggle(!task.completed)}
        className={cn(
          'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border transition-colors',
          task.completed
            ? 'border-primary bg-primary text-white'
            : 'border-border bg-background text-textMuted hover:border-primary hover:text-primary',
          disabled && 'cursor-not-allowed opacity-60',
        )}
      >
        {task.completed ? <Check className="h-5 w-5" /> : null}
      </button>
    </Card>
  )
}
