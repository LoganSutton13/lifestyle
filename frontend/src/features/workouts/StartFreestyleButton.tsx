import { Button } from '../../components/ui/Button'

export interface StartFreestyleButtonProps {
  disabled?: boolean
  loading?: boolean
  onStart: () => void
}

export function StartFreestyleButton({ disabled, loading, onStart }: StartFreestyleButtonProps) {
  return (
    <Button className="w-full" disabled={disabled} loading={loading} onClick={onStart}>
      Start Freestyle Workout
    </Button>
  )
}
