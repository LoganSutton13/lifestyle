import { useEffect, useState } from 'react'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { MutedText } from '../../components/ui/MutedText'
import { SectionTitle } from '../../components/ui/SectionTitle'
import { Textarea } from '../../components/ui/Textarea'

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
    <Card className="space-y-3">
      <div>
        <SectionTitle>Daily Notes</SectionTitle>
        <MutedText>Share how your day went with your coach.</MutedText>
      </div>
      <Textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        rows={4}
        placeholder="How did today go?"
      />
      <div className="flex items-center justify-between gap-3">
        <Button type="button" onClick={handleSave} loading={saving}>
          Save note
        </Button>
        {savedMessage ? <span className="text-sm text-success">{savedMessage}</span> : null}
        {!savedMessage && updatedAt ? (
          <MutedText as="span" size="xs">
            Last updated {new Date(updatedAt).toLocaleString()}
          </MutedText>
        ) : null}
      </div>
    </Card>
  )
}
