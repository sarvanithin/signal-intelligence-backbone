import React, { useEffect, useState } from 'react'
import { fetchSummary, fetchDrift, fetchAnomalies, fetchAnomalyById } from './api'
import AgentStatusRow from './components/AgentStatusRow'
import DriftTrendChart from './components/DriftTrendChart'
import AnomalyTimeline from './components/AnomalyTimeline'
import DetailsDrawer from './components/DetailsDrawer'
import Banner from './components/Banner'

export default function App() {
  const [summary, setSummary] = useState([])
  const [selected, setSelected] = useState(null)
  const [drift, setDrift] = useState([])
  const [anoms, setAnoms] = useState([])
  const [selectedEvt, setSelectedEvt] = useState(null)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(false)

  const pollMs = Number(import.meta.env.VITE_POLL_MS || 5000)
  const isDemo = (import.meta.env.VITE_DEMO || 'true') === 'true'

  async function load(agent) {
    setLoading(true)
    try {
      const s = await fetchSummary()
      setSummary(s)

      const selectedAgent = agent || selected || s?.[0]?.agent
      setSelected(selectedAgent)

      if (selectedAgent) {
        const [d, e] = await Promise.all([
          fetchDrift(selectedAgent),
          fetchAnomalies(selectedAgent)
        ])
        setDrift(d.series || [])
        setAnoms(e || [])
      }

      setErr(null)
    } catch (e) {
      setErr(`Unable to fetch data: ${e.message}. Retrying...`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(selected)
  }, [])

  useEffect(() => {
    if (selected) {
      load(selected)
      const id = setInterval(() => load(selected), pollMs)
      return () => clearInterval(id)
    }
  }, [selected, pollMs])

  const handleSelectEvent = async (id) => {
    try {
      const evt = await fetchAnomalyById(id)
      setSelectedEvt(evt)
    } catch (e) {
      setErr(`Failed to load event details: ${e.message}`)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <header className="border-b border-slate-700 bg-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Coherence Console</h1>
              <p className="text-sm text-slate-400 mt-1">
                Real-time agent coherence monitoring
                {isDemo && <span className="ml-2 inline-block px-2 py-1 bg-yellow-900 text-yellow-100 rounded text-xs">DEMO MODE</span>}
              </p>
            </div>
            <div className="text-right text-xs text-slate-400">
              <div>Polling every {pollMs}ms</div>
              {loading && <div className="text-blue-400">● Updating...</div>}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {err && <Banner kind="error" text={err} />}

        <AgentStatusRow data={summary} selected={selected} onSelect={setSelected} />

        {selected && (
          <>
            <DriftTrendChart data={drift} />
            <AnomalyTimeline items={anoms} onSelect={handleSelectEvent} />
          </>
        )}

        <DetailsDrawer open={!!selectedEvt} onClose={() => setSelectedEvt(null)} payload={selectedEvt} />
      </main>
    </div>
  )
}
