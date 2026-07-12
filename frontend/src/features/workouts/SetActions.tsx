import { ArrowDownToLine, Plus, Trash2 } from 'lucide-react'
import { Button } from '../../components/ui/Button'

export interface SetActionsProps {
  onAddSet: () => void
  onDropSet: () => void
  onRemoveSet: () => void
  canRemove: boolean
  disabled?: boolean
}

export function SetActions({ onAddSet, onDropSet, onRemoveSet, canRemove, disabled }: SetActionsProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      <Button variant="secondary" size="sm" disabled={disabled} onClick={onAddSet}>
        <Plus className="h-4 w-4" aria-hidden="true" />
        Add Set
      </Button>
      <Button variant="secondary" size="sm" disabled={disabled} onClick={onDropSet}>
        <ArrowDownToLine className="h-4 w-4" aria-hidden="true" />
        Drop Set
      </Button>
      <Button
        variant="secondary"
        size="sm"
        disabled={disabled || !canRemove}
        onClick={onRemoveSet}
        className="text-danger"
      >
        <Trash2 className="h-4 w-4" aria-hidden="true" />
        Remove
      </Button>
    </div>
  )
}
