import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from '../../components/ui/Card'
import { Spinner } from '../../components/ui/Spinner'
import { formatDisplayDate } from '../../lib/date'
import { RANGE_PRESETS, type RangePresetKey } from '../../lib/constants'
import { getRangeFromPreset } from '../../lib/date'
import { RangeFilter } from '../measurements/RangeFilter'
import * as coachApi from './api'

export function CoachNotesPanel({ clientId }: { clientId: string }) {
  const [rangePreset, setRangePreset] = useState<RangePresetKey>('1M')

  const range = useMemo(() => {
    const preset = RANGE_PRESETS.find((item) => item.key === rangePreset)
    return getRangeFromPreset(preset?.months ?? 1)
  }, [rangePreset])

  const historyQuery = useQuery({
    queryKey: ['coach-checklist-history', clientId, range],
    queryFn: () => coachApi.fetchChecklistHistory(clientId, range),
  })

  const notesQuery = useQuery({
    queryKey: ['coach-daily-notes', clientId, range],
    queryFn: () => coachApi.fetchDailyNotes(clientId, range),
  })

  return (
    <div className="space-y-4">
      <RangeFilter value={rangePreset} onChange={setRangePreset} />

      {historyQuery.isLoading || notesQuery.isLoading ? (
        <Spinner label="Loading history..." />
      ) : null}

      {historyQuery.isSuccess ? (
        <section className="space-y-2">
          <h3 className="font-semibold text-text">Checklist completion</h3>
          {historyQuery.data.items.length === 0 ? (
            <p className="text-sm text-textMuted">No checklist history in this range.</p>
          ) : (
            historyQuery.data.items.map((day) => (
              <Card key={day.date} className="flex items-center justify-between">
                <span className="text-sm text-text">{formatDisplayDate(day.date)}</span>
                <span className="text-sm text-textMuted">
                  {day.completedTasks}/{day.totalTasks} completed
                </span>
              </Card>
            ))
          )}
        </section>
      ) : null}

      {notesQuery.isSuccess ? (
        <section className="space-y-2">
          <h3 className="font-semibold text-text">Daily notes</h3>
          {notesQuery.data.items.length === 0 ? (
            <p className="text-sm text-textMuted">No notes in this range.</p>
          ) : (
            notesQuery.data.items.map((note) => (
              <Card key={note.date}>
                <p className="text-sm font-medium text-text">{formatDisplayDate(note.date)}</p>
                <p className="mt-1 whitespace-pre-wrap text-sm text-textMuted">{note.body}</p>
              </Card>
            ))
          )}
        </section>
      ) : null}
    </div>
  )
}
