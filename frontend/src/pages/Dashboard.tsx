import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { api } from '../hooks/useApi'
import NewRunModal from './NewRunModal'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null as any)
  const [runs, setRuns] = useState([] as any[])
  const [showNewRun, setShowNewRun] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getStats(), api.listRuns()])
      .then(([s, r]) => { setStats(s.data); setRuns(r.data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <nav className="navbar">
        <span className="brand">LeadGen</span>
        <a href="/" className="active">Dashboard</a>
        <a href="/runs">Runs</a>
        <span className="user">{user?.name} · {user?.email}</span>
        <a href="#" onClick={() => { logout(); navigate('/login') }}>Logout</a>
      </nav>
      <div className="container">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700 }}>Welcome back, {user?.name}</h1>
          <button className="btn btn-primary" onClick={() => setShowNewRun(true)}>+ New Run</button>
        </div>
        {loading ? <p>Loading...</p> : stats && (
          <div className="stat-grid">
            <div className="stat-card">
              <div className="label">Total Runs</div>
              <div className="value">{stats.total_runs}</div>
            </div>
            <div className="stat-card">
              <div className="label">Total Leads</div>
              <div className="value">{stats.total_leads}</div>
            </div>
            <div className="stat-card">
              <div className="label">Tier A Leads</div>
              <div className="value" style={{ color: '#16a34a' }}>{stats.tier_a}</div>
            </div>
            <div className="stat-card">
              <div className="label">Tier B Leads</div>
              <div className="value" style={{ color: '#ca8a04' }}>{stats.tier_b}</div>
            </div>
            <div className="stat-card">
              <div className="label">Contacted</div>
              <div className="value">{stats.contacted}</div>
            </div>
            <div className="stat-card">
              <div className="label">Won</div>
              <div className="value" style={{ color: '#059669' }}>{stats.won}</div>
            </div>
          </div>
        )}
        <div className="card">
          <h2>Recent Runs</h2>
          {runs.length === 0 ? (
            <p className="text-muted">No runs yet. Click "New Run" to get started.</p>
          ) : (
            <table>
              <thead><tr><th>Market</th><th>Vertical</th><th>Status</th><th>Total</th><th>Tier A</th><th>Created</th></tr></thead>
              <tbody>
                {runs.slice(0, 10).map((r: any) => (
                  <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/runs/${r.id}`)}>
                    <td>{r.market}</td>
                    <td>{r.vertical}</td>
                    <td><span className={`badge badge-${r.status === 'completed' ? 'verified' : r.status === 'running' ? 'new' : 'c'}`}>{r.status}</span></td>
                    <td>{r.total_leads}</td>
                    <td>{r.tier_a}</td>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
      {showNewRun && <NewRunModal onClose={() => setShowNewRun(false)} />}
    </div>
  )
}
