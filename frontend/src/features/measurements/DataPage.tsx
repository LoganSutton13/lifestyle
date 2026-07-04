import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Spinner } from '../../components/ui/Spinner'
import { useToast } from '../../components/ui/Toast'
import { MAX_MEASUREMENT_RANGE_DAYS, RANGE_PRESETS, type RangePresetKey } from '../../lib/constants'
import { daysBetween, formatDateTimeForApi, getRangeFromPreset } from '../../lib/date'
import { getDefaultUnitForType } from '../../lib/units'
import { getErrorMessage } from '../../lib/errors'
import * as measurementsApi from './api'
import { AddMeasurementModal, type AddMeasurementForm } from './AddMeasurementModal'
import { MeasurementChart } from './MeasurementChart'
import { MeasurementTypeTabs } from './MeasurementTypeTabs'
import { RangeFilter } from './RangeFilter'

export function DataPage() {
  const [rangePreset, setRangePreset] = useState<RangePresetKey>('1M')
  const [typeKey, setTypeKey] = useState<string>('body_weight')
  const [modalOpen, setModalOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const typesQuery = useQuery({
    queryKey: ['measurement-types'],
    queryFn: measurementsApi.fetchMeasurementTypes,
  })

  const activeTypeKey = useMemo(() => {
    if (typesQuery.data?.items.some((type) => type.key === typeKey)) {
      return typeKey
    }
    return typesQuery.data?.items[0]?.key ?? 'body_weight'
  }, [typeKey, typesQuery.data])

  const range = useMemo(() => {
    const preset = RANGE_PRESETS.find((item) => item.key === rangePreset)
    return getRangeFromPreset(preset?.months ?? 1)
  }, [rangePreset])

  const unitKey = getDefaultUnitForType(activeTypeKey)

  const graphQuery = useQuery({
    queryKey: ['measurements', activeTypeKey, range.startDate, range.endDate, unitKey],
    queryFn: () =>
      measurementsApi.fetchMeasurements({
        typeKey: activeTypeKey,
        startDate: range.startDate,
        endDate: range.endDate,
        unitKey,
      }),
    enabled: !!activeTypeKey,
  })

  const createMutation = useMutation({
    mutationFn: (values: AddMeasurementForm) => {
      const span = daysBetween(range.startDate, range.endDate)
      if (span > MAX_MEASUREMENT_RANGE_DAYS) {
        throw new Error('Date range cannot exceed 3 years')
      }

      return measurementsApi.createMeasurement({
        typeKey: values.typeKey,
        value: values.value,
        unitKey: values.unitKey,
        recordedAt: formatDateTimeForApi(new Date(values.recordedAt)),
      })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['measurements'] })
      setModalOpen(false)
      showToast('Measurement saved')
    },
    onError: (error) => {
      showToast(getErrorMessage(error), 'error')
    },
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-text">Data</h1>
        <button
          type="button"
          aria-label="Add measurement"
          onClick={() => setModalOpen(true)}
          className="flex min-h-touch min-w-touch items-center justify-center rounded-full bg-primary text-white hover:bg-primaryDark"
        >
          <Plus className="h-5 w-5" />
        </button>
      </div>

      {typesQuery.isLoading ? <Spinner label="Loading measurement types..." /> : null}

      {typesQuery.isSuccess ? (
        <MeasurementTypeTabs
          types={typesQuery.data.items}
          value={activeTypeKey}
          onChange={setTypeKey}
        />
      ) : null}

      <RangeFilter value={rangePreset} onChange={setRangePreset} />

      {graphQuery.isLoading ? <Spinner label="Loading chart..." /> : null}

      {graphQuery.isError ? (
        <p className="rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          {getErrorMessage(graphQuery.error)}
        </p>
      ) : null}

      {graphQuery.isSuccess ? <MeasurementChart data={graphQuery.data} /> : null}

      {typesQuery.isSuccess ? (
        <AddMeasurementModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          types={typesQuery.data.items}
          defaultTypeKey={activeTypeKey}
          saving={createMutation.isPending}
          onSubmit={(values) => createMutation.mutate(values)}
        />
      ) : null}
    </div>
  )
}
