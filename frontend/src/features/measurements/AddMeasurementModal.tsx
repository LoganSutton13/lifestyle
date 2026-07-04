import { useEffect } from 'react'
import { useForm, type Resolver } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { Select } from '../../components/ui/Select'
import { getDefaultUnitForType, getUnitsForType } from '../../lib/units'
import type { MeasurementType } from './api'

const schema = z.object({
  value: z.coerce.number().positive('Value must be greater than zero'),
  typeKey: z.string().min(1, 'Type is required'),
  unitKey: z.string().min(1, 'Unit is required'),
  recordedAt: z.string().min(1, 'Date is required'),
})

export type AddMeasurementForm = z.infer<typeof schema>

export interface AddMeasurementModalProps {
  open: boolean
  onClose: () => void
  types: MeasurementType[]
  defaultTypeKey: string
  saving?: boolean
  onSubmit: (values: AddMeasurementForm) => void
}

export function AddMeasurementModal({
  open,
  onClose,
  types,
  defaultTypeKey,
  saving,
  onSubmit,
}: AddMeasurementModalProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<AddMeasurementForm>({
    resolver: zodResolver(schema) as Resolver<AddMeasurementForm>,
    defaultValues: {
      typeKey: defaultTypeKey,
      unitKey: getDefaultUnitForType(defaultTypeKey),
      recordedAt: new Date().toISOString().slice(0, 16),
    },
  })

  const typeKey = watch('typeKey')

  useEffect(() => {
    if (open) {
      reset({
        typeKey: defaultTypeKey,
        unitKey: getDefaultUnitForType(defaultTypeKey),
        recordedAt: new Date().toISOString().slice(0, 16),
      })
    }
  }, [open, defaultTypeKey, reset])

  useEffect(() => {
    setValue('unitKey', getDefaultUnitForType(typeKey))
  }, [typeKey, setValue])

  const unitOptions = getUnitsForType(typeKey).map((unit) => ({
    value: unit.key,
    label: `${unit.label} (${unit.symbol})`,
  }))

  const typeOptions = types.map((type) => ({
    value: type.key,
    label: type.displayName,
  }))

  return (
    <Modal open={open} onClose={onClose} title="Add Measurement">
      <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
        <Select
          label="Data type"
          options={typeOptions}
          error={errors.typeKey?.message}
          {...register('typeKey')}
        />
        <Input
          label="Value"
          type="number"
          step="0.1"
          inputMode="decimal"
          error={errors.value?.message}
          {...register('value')}
        />
        <Select
          label="Unit"
          options={unitOptions}
          error={errors.unitKey?.message}
          {...register('unitKey')}
        />
        <Input
          label="Recorded at"
          type="datetime-local"
          error={errors.recordedAt?.message}
          {...register('recordedAt')}
        />
        <div className="flex gap-3 pt-2">
          <Button type="button" variant="secondary" className="flex-1" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" className="flex-1" loading={saving}>
            Save
          </Button>
        </div>
      </form>
    </Modal>
  )
}
