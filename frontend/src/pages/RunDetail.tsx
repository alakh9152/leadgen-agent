import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { api } from '../hooks/useApi'

export default function RunDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [run, setRun] = useState(null as any)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getRun(id!).then(r => setRun(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="page-center">Loading...</div>
  if (!run) return <div className="page-center">Run not found</div>

  return (
    <div>
      <nav className="navbar">
        <span className="brand">LeadGen</span>
        <a href="/">Dashboard</a>
        <a href="/runs">Runs</a>
        <span className="user">{user?.name}</span>
        <a href="#" onClick={() => { logout(); navigate('/login') }}>Logout</a>
      </nav>
      <div className="container">
        <button className="btn btn-secondary" onClick={() => navigate('/runs')} style={{ marginBottom: 16 }}>← Back</button>
        <div className="card">
          <h2>{run.market}</h2>
          <div className="stat-grid" style={{ marginTop: 16 }}>
            <div className="stat-card"><div className="label">Status</div><div className="value" style={{ fontSize: 18 }}>{run.status}</div></div>
            <div className="stat-card"><div className="label">Total Leads</div><div className="value">{run.total_leads}</div></div>
            <div className="stat-card"><div className="label">Tier A</div><div className="value" style={{ color: '#16a34a' }}>{run.tier_a}</div></div>
            <div className="stat-card"><div className="label">Tier B</div><div className="value" style={{ color: '#ca8a04' }}>{run.tier_b}</div></div>
            <div className="stat-card"><div className="label">Tier C</div><div className="value">{run.tier_c}</div></div>
          </div>
          {run.error && <div style={{ background: '#fee2e2', color: '#dc2626', padding: 12, borderRadius: 8, marginTop: 16, fontSize: 13 }}>Error: {run.error}</div>}
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <button className="btn btn-primary" onClick={() => navigate(`/runs/${id}/leads`)}>View Leads ({run.total_leads})</button>
          <a className="btn btn-secondary" href={`/api/runs/${id}/export/csv`} download>Export CSV</a>
          <a className="btn btn-secondary" href={`/api/runs/${id}/export/xlsx`} download>Export XLSX</a>
        </div>
      </div>
    </div>
  )
}
