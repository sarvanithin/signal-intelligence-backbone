import React, { useState } from 'react'
import { SEVERITY_COLOR, formatScore } from '../lib/statusTokens'

export default function AnomalyTimeline({ items, onSelect }) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const pageCount = Math.ceil((items?.length || 0) / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const paginatedItems = items?.slice(startIdx, startIdx + itemsPerPage) || [];

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Event Timeline (Last 60 min)</h2>
      <div className="coherence-table">
        {items && items.length > 0 ? (
          <>
            <table className="w-full text-sm">
              <thead className="bg-slate-900 border-b border-slate-700">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold">Time</th>
                  <th className="text-left px-4 py-3 font-semibold">Agent</th>
                  <th className="text-right px-4 py-3 font-semibold">Variance</th>
                  <th className="text-center px-4 py-3 font-semibold">Severity</th>
                </tr>
              </thead>
              <tbody>
                {paginatedItems.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => onSelect(item.id)}
                    className="border-t border-slate-700 hover:bg-slate-700 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-3 text-slate-300 font-mono text-xs">
                      {new Date(item.ts).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-3 font-semibold">{item.agent}</td>
                    <td className="px-4 py-3 text-right font-mono">{formatScore(item.variance_percent / 100)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block w-3 h-3 rounded-full ${SEVERITY_COLOR[item.severity] || 'bg-gray-400'}`}></span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {pageCount > 1 && (
              <div className="flex items-center justify-center gap-2 p-3 border-t border-slate-700">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm bg-slate-700 rounded disabled:opacity-50"
                >
                  ← Prev
                </button>
                <span className="text-sm text-slate-400">
                  Page {currentPage} of {pageCount}
                </span>
                <button
                  onClick={() => setCurrentPage(Math.min(pageCount, currentPage + 1))}
                  disabled={currentPage === pageCount}
                  className="px-3 py-1 text-sm bg-slate-700 rounded disabled:opacity-50"
                >
                  Next →
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="p-8 text-center text-slate-400">No anomalies detected</div>
        )}
      </div>
    </div>
  )
}
