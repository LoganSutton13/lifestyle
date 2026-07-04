import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatDisplayDate } from '../../lib/date'
import type { MeasurementGraphResponse } from './api'

export interface MeasurementChartProps {
  data: MeasurementGraphResponse
}

export function MeasurementChart({ data }: MeasurementChartProps) {
  const chartData = data.points.map((point) => ({
    ...point,
    label: formatDisplayDate(point.recordedAt),
  }))

  if (chartData.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-border bg-surface text-sm text-textMuted">
        No measurements in this range
      </div>
    )
  }

  return (
    <div className="h-64 w-full rounded-2xl border border-border bg-surfaceElevated p-3">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
          <YAxis
            tick={{ fontSize: 11 }}
            domain={['auto', 'auto']}
            label={{
              value: data.unit.symbol,
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 11, fill: '#4B5563' },
            }}
          />
          <Tooltip
            formatter={(value) => [`${String(value)} ${data.unit.symbol}`, data.type.displayName]}
            labelFormatter={(label) => String(label)}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#00B8D9"
            strokeWidth={2}
            dot={{ fill: '#00B8D9', r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
