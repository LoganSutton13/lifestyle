import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { MutedText } from '../../components/ui/MutedText'
import { PageTitle } from '../../components/ui/PageTitle'
import { PillTabs } from '../../components/ui/PillTabs'
import { CoachMealsPanel } from './CoachMealsPanel'
import { CoachMeasurementsPanel } from './CoachMeasurementsPanel'
import { CoachNotesPanel } from './CoachNotesPanel'
import { CoachTasksPanel } from './CoachTasksPanel'
import { CoachWorkoutsPanel } from './workouts/CoachWorkoutsPanel'

const tabs = [
  { value: 'overview', label: 'Overview' },
  { value: 'meals', label: 'Meals' },
  { value: 'tasks', label: 'Daily Activities' },
  { value: 'workouts', label: 'Workouts' },
  { value: 'measurements', label: 'Measurements' },
  { value: 'notes', label: 'History / Notes' },
] as const

type TabKey = (typeof tabs)[number]['value']

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

      <PageTitle>Client dashboard</PageTitle>

      <PillTabs
        options={[...tabs]}
        value={activeTab}
        onChange={setActiveTab}
        ariaLabel="Client sections"
        layout="scroll"
      />

      {activeTab === 'overview' ? (
        <MutedText>
          Use the tabs above to manage meals, daily activities, workouts, measurements, and notes for this
          client.
        </MutedText>
      ) : null}
      {activeTab === 'meals' ? <CoachMealsPanel clientId={clientId} /> : null}
      {activeTab === 'tasks' ? <CoachTasksPanel clientId={clientId} /> : null}
      {activeTab === 'workouts' ? <CoachWorkoutsPanel clientId={clientId} /> : null}
      {activeTab === 'measurements' ? <CoachMeasurementsPanel clientId={clientId} /> : null}
      {activeTab === 'notes' ? <CoachNotesPanel clientId={clientId} /> : null}
    </div>
  )
}
