import { useEffect, useState } from 'react'
import { Button } from '../../components/ui/Button'

export interface DailyNoteBoxProps {
  value: string
  updatedAt: string | null
  saving?: boolean
  onSave: (body: string) => void
}

export function DailyNoteBox({ value, updatedAt, saving, onSave }: DailyNoteBoxProps) {
  const [body, setBody] = useState(value)
  const [savedMessage, setSavedMessage] = useState<string | null>(null)

  useEffect(() => {
    setBody(value)
  }, [value])

  const handleSave = () => {
    onSave(body)
    setSavedMessage('Note saved')
    window.setTimeout(() => setSavedMessage(null), 2500)
  }

  return (
    <section className="space-y-3 rounded-2xl border border-border bg-surfaceElevated p-4">
      <div>
        <h2 className="text-lg font-semibold text-text">Daily Notes</h2>
        <p className="text-sm text-textMuted">Share how your day went with your coach.</p>
      </div>
      <textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        rows={4}
        placeholder="How did today go?"
        className="w-full rounded-xl border border-border bg-background px-3 py-2.5 text-base text-text outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
      />
      <div className="flex items-center justify-between gap-3">
        <Button type="button" onClick={handleSave} loading={saving}>
          Save note
        </Button>
        {savedMessage ? <span className="text-sm text-success">{savedMessage}</span> : null}
        {!savedMessage && updatedAt ? (
          <span className="text-xs text-textMuted">Last updated {new Date(updatedAt).toLocaleString()}</span>
        ) : null}
      </div>
    </section>
  )
}
