import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'

export interface DiscardWorkoutDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  submitting?: boolean
}

export function DiscardWorkoutDialog({ open, onClose, onConfirm, submitting }: DiscardWorkoutDialogProps) {
  if (!open) {
    return null
  }

  return (
    <Modal open={open} onClose={onClose} title="Discard this workout?">
      <div className="flex flex-col gap-4">
        <p className="text-sm text-textMuted">
          All exercises and sets in this active workout will be deleted. This cannot be undone.
        </p>
        <div className="flex gap-3">
          <Button variant="secondary" className="flex-1" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" className="flex-1" loading={submitting} onClick={onConfirm}>
            Discard Workout
          </Button>
        </div>
      </div>
    </Modal>
  )
}
