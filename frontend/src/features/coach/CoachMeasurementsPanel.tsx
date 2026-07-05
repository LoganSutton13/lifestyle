import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Spinner } from '../../components/ui/Spinner'
import { RANGE_PRESETS, type RangePresetKey } from '../../lib/constants'
import { getBrowserTimezone, getRangeFromPreset } from '../../lib/date'
import { getDefaultUnitForType } from '../../lib/units'
import { MeasurementChart } from '../measurements/MeasurementChart'
import { MeasurementTypeTabs } from '../measurements/MeasurementTypeTabs'
import { RangeFilter } from '../measurements/RangeFilter'
import * as coachApi from './api'

export function CoachMeasurementsPanel({ clientId }: { clientId: string }) {
  const [rangePreset, setRangePreset] = useState<RangePresetKey>('1M')
  const [typeKey, setTypeKey] = useState('body_weight')

  const clientQuery = useQuery({
    queryKey: ['coach-client', clientId],
    queryFn: () => coachApi.fetchCoachClient(clientId),
  })

  const timezone = clientQuery.data?.timezone ?? getBrowserTimezone()

  const typesQuery = useQuery({
    queryKey: ['coach-client-measurement-types', clientId],
    queryFn: () => coachApi.fetchClientMeasurementTypes(clientId),
  })

  const activeTypeKey = useMemo(() => {
    if (typesQuery.data?.items.some((type) => type.key === typeKey)) {
      return typeKey
    }
    return typesQuery.data?.items[0]?.key ?? 'body_weight'
  }, [typeKey, typesQuery.data])

  const range = useMemo(() => {
    const preset = RANGE_PRESETS.find((item) => item.key === rangePreset)
    return getRangeFromPreset(preset?.months ?? 1, timezone)
  }, [rangePreset, timezone])

  const graphQuery = useQuery({
    queryKey: ['coach-client-measurements', clientId, activeTypeKey, range],
    queryFn: () =>
      coachApi.fetchClientMeasurements(clientId, {
        typeKey: activeTypeKey,
        startDate: range.startDate,
        endDate: range.endDate,
        unitKey: getDefaultUnitForType(activeTypeKey),
      }),
    enabled: !!activeTypeKey,
  })

  return (
    <div className="space-y-4">
      {typesQuery.isLoading ? <Spinner label="Loading types..." /> : null}
      {typesQuery.isSuccess ? (
        <MeasurementTypeTabs
          types={typesQuery.data.items}
          value={activeTypeKey}
          onChange={setTypeKey}
        />
      ) : null}
      <RangeFilter value={rangePreset} onChange={setRangePreset} />
      {graphQuery.isLoading ? <Spinner label="Loading chart..." /> : null}
      {graphQuery.isSuccess ? <MeasurementChart data={graphQuery.data} timezone={timezone} /> : null}
    </div>
  )
}
