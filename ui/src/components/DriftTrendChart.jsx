import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function DriftTrendChart({ data }) {
  const chartData = data && data.length > 0
    ? data.map((point) => ({
        ...point,
        time: new Date(point.t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }))
    : [];

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Drift Trend (Last 60 min)</h2>
      <div className="coherence-chart">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis
                dataKey="time"
                stroke="#94a3b8"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                domain={[0, 1]}
                stroke="#94a3b8"
                style={{ fontSize: '12px' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '6px'
                }}
                formatter={(value) => value.toFixed(3)}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                dot={{ fill: '#3b82f6', r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-80 flex items-center justify-center text-slate-400">
            No drift data available
          </div>
        )}
      </div>
    </div>
  )
}
