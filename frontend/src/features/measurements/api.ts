import { apiRequest } from '../../lib/apiClient'

export interface MeasurementType {
  key: string
  displayName: string
}

export interface MeasurementTypesResponse {
  items: MeasurementType[]
}

export interface MeasurementPoint {
  id: string
  recordedAt: string
  value: number
}

export interface MeasurementGraphResponse {
  type: MeasurementType
  unit: { key: string; symbol: string }
  startDate: string
  endDate: string
  points: MeasurementPoint[]
}

export interface CreateMeasurementPayload {
  typeKey: string
  value: number
  unitKey: string
  recordedAt: string
}

export function fetchMeasurementTypes(): Promise<MeasurementTypesResponse> {
  return apiRequest<MeasurementTypesResponse>('/api/me/measurement-types')
}

export function fetchMeasurements(params: {
  typeKey: string
  startDate: string
  endDate: string
  unitKey: string
}): Promise<MeasurementGraphResponse> {
  const search = new URLSearchParams({
    typeKey: params.typeKey,
    startDate: params.startDate,
    endDate: params.endDate,
    unitKey: params.unitKey,
  })
  return apiRequest<MeasurementGraphResponse>(`/api/me/measurements?${search.toString()}`)
}

export function createMeasurement(payload: CreateMeasurementPayload): Promise<void> {
  return apiRequest<void>('/api/me/measurements', {
    method: 'POST',
    body: payload,
  })
}
