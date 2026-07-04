import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { cn } from '../../lib/cn'
import { CoachMealsPanel } from './CoachMealsPanel'
import { CoachMeasurementsPanel } from './CoachMeasurementsPanel'
import { CoachNotesPanel } from './CoachNotesPanel'
import { CoachTasksPanel } from './CoachTasksPanel'

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'meals', label: 'Meals' },
  { key: 'tasks', label: 'Daily Activities' },
  { key: 'measurements', label: 'Measurements' },
  { key: 'notes', label: 'History / Notes' },
] as const

type TabKey = (typeof tabs)[number]['key']

export function CoachClientDetail() {
  const { clientId = '' } = useParams()
  const [activeTab, setActiveTab] = useState<TabKey>('overview')

  return (
    <div className="space-y-5">
      <Link
        to="/coach"
        className="inline-flex min-h-touch items-center gap-2 text-sm font-medium text-primary hover:text-primaryDark"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to clients
      </Link>

      <h1 className="text-2xl font-bold text-text">Client dashboard</h1>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'min-h-touch shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-primary text-white'
                : 'bg-surface text-textMuted hover:bg-primarySoft hover:text-primaryDark',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' ? (
        <p className="text-sm text-textMuted">
          Use the tabs above to manage meals, daily activities, measurements, and notes for this client.
        </p>
      ) : null}
      {activeTab === 'meals' ? <CoachMealsPanel clientId={clientId} /> : null}
      {activeTab === 'tasks' ? <CoachTasksPanel clientId={clientId} /> : null}
      {activeTab === 'measurements' ? <CoachMeasurementsPanel clientId={clientId} /> : null}
      {activeTab === 'notes' ? <CoachNotesPanel clientId={clientId} /> : null}
    </div>
  )
}
