import React from 'react'
import { SEVERITY_COLOR, formatScore } from '../lib/statusTokens'

export default function DetailsDrawer({ open, onClose, payload }) {
  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      ></div>
      <div className="coherence-drawer">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold">Event Details</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {payload ? (
          <div className="overflow-y-auto h-[calc(100%-60px)] p-4 space-y-4">
            <div className="space-y-2">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Agent</div>
              <div className="font-semibold text-lg">{payload.agent}</div>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Timestamp</div>
              <div className="font-mono text-sm">{new Date(payload.ts).toLocaleString()}</div>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Severity</div>
              <div className="flex items-center gap-2">
                <span className={`inline-block w-4 h-4 rounded-full ${SEVERITY_COLOR[payload.severity] || 'bg-gray-400'}`}></span>
                <span className="font-semibold capitalize">{payload.severity}</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Variance</div>
              <div className="font-mono text-lg font-semibold">{formatScore(payload.variance_percent / 100)}</div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-700 rounded p-3 space-y-1">
                <div className="text-xs text-slate-400">Baseline</div>
                <div className="font-mono font-semibold">{formatScore(payload.baseline_value)}</div>
              </div>
              <div className="bg-slate-700 rounded p-3 space-y-1">
                <div className="text-xs text-slate-400">Current</div>
                <div className="font-mono font-semibold">{formatScore(payload.current_value)}</div>
              </div>
            </div>

            {payload.biometric_data && (
              <div className="space-y-2 bg-slate-700 rounded p-3">
                <div className="text-xs text-slate-400 uppercase tracking-wide">Biometrics</div>
                <div className="space-y-1 font-mono text-sm">
                  {payload.biometric_data.hrv && (
                    <div className="flex justify-between">
                      <span>HRV:</span>
                      <span>{payload.biometric_data.hrv} ms</span>
                    </div>
                  )}
                  {payload.biometric_data.gsr && (
                    <div className="flex justify-between">
                      <span>GSR:</span>
                      <span>{payload.biometric_data.gsr} μS</span>
                    </div>
                  )}
                  {payload.biometric_data.skin_temperature && (
                    <div className="flex justify-between">
                      <span>Temp:</span>
                      <span>{payload.biometric_data.skin_temperature}°C</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {payload.interpretation && (
              <div className="space-y-2">
                <div className="text-xs text-slate-400 uppercase tracking-wide">Interpretation</div>
                <p className="text-sm leading-relaxed text-slate-300">{payload.interpretation}</p>
              </div>
            )}

            <button
              onClick={() => {
                navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
                alert('JSON copied to clipboard');
              }}
              className="w-full mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
            >
              Copy JSON
            </button>
          </div>
        ) : (
          <div className="p-4 text-slate-400">Loading...</div>
        )}
      </div>
    </>
  )
}
