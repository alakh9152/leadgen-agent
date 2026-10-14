import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { api } from '../hooks/useApi'
import NewRunModal from './NewRunModal'

export default function Runs() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [runs, setRuns] = useState([] as any[])
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)

  useEffect(() => { api.listRuns().then(r => setRuns(r.data)).catch(() => {}).finally(() => setLoading(false)) }, [])

  return (
    <div>
      <nav className="navbar">
        <span className="brand">LeadGen</span>
        <a href="/">Dashboard</a>
        <a href="/runs" className="active">Runs</a>
        <span className="user">{user?.name}</span>
        <a href="#" onClick={() => { logout(); navigate('/login') }}>Logout</a>
      </nav>
      <div className="container">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700 }}>All Runs</h1>
          <button className="btn btn-primary" onClick={() => setShowNew(true)}>+ New Run</button>
        </div>
        {loading ? <p>Loading...</p> : runs.length === 0 ? (
          <div className="card"><p className="text-muted">No runs yet. Click "New Run" to get started.</p></div>
        ) : (
          <div className="card">
            <table>
              <thead><tr><th>Market</th><th>Vertical</th><th>Status</th><th>Total</th><th>Tier A</th><th>Tier B</th><th>Created</th><th></th></tr></thead>
              <tbody>
                {runs.map((r: any) => (
                  <tr key={r.id}>
                    <td>{r.market}</td>
                    <td>{r.vertical}</td>
                    <td><span className={`badge badge-${r.status === 'completed' ? 'verified' : r.status === 'running' ? 'new' : 'c'}`}>{r.status}</span></td>
                    <td>{r.total_leads}</td>
                    <td>{r.tier_a}</td>
                    <td>{r.tier_b}</td>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                    <td><a className="link" onClick={() => navigate(`/runs/${r.id}`)}>View</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {showNew && <NewRunModal onClose={() => setShowNew(false)} />}
    </div>
  )
}
