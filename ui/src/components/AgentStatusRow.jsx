import React from 'react'
import { STATUS_COLOR, formatScore, getStatusLabel } from '../lib/statusTokens'

export default function AgentStatusRow({ data, selected, onSelect }) {
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Agent Status</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        {data && data.length > 0 ? (
          data.map((agent) => {
            const colors = STATUS_COLOR[agent.drift_status] || STATUS_COLOR.stable;
            const isSelected = selected === agent.agent;
            return (
              <button
                key={agent.agent}
                onClick={() => onSelect(agent.agent)}
                className={`coherence-card transition-all cursor-pointer ${
                  isSelected ? 'ring-2 ring-blue-400' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-sm">{agent.agent}</h3>
                  <div className={`status-badge ${colors.bg} ${colors.text}`}>
                    {getStatusLabel(agent.drift_status)}
                  </div>
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Coherence</span>
                    <span className="font-mono font-semibold">{formatScore(agent.coherence_score)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Signals</span>
                    <span className="font-mono">{agent.signal_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Strength</span>
                    <span className="font-mono">{formatScore(agent.avg_signal_strength)}</span>
                  </div>
                </div>
              </button>
            )
          })
        ) : (
          <div className="col-span-full text-slate-400 text-sm">No agent data available</div>
        )}
      </div>
    </div>
  )
}
