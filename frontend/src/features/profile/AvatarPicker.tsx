import { cn } from '../../lib/cn'
import { AVATAR_KEYS, avatarUrl } from '../../lib/constants'

export interface AvatarPickerProps {
  value: string
  onChange: (avatarKey: string) => void
}

export function AvatarPicker({ value, onChange }: AvatarPickerProps) {
  return (
    <div className="grid grid-cols-4 gap-3 sm:grid-cols-6">
      {AVATAR_KEYS.map((key) => (
        <button
          key={key}
          type="button"
          aria-label={`Select ${key} avatar`}
          aria-pressed={value === key}
          onClick={() => onChange(key)}
          className={cn(
            'flex aspect-square items-center justify-center rounded-2xl border p-2 transition-colors',
            value === key ? 'border-primary bg-primarySoft' : 'border-border bg-surface hover:border-primary/50',
          )}
        >
          <img src={avatarUrl(key)} alt="" className="h-12 w-12" />
        </button>
      ))}
    </div>
  )
}
