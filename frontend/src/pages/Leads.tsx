import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { api, LeadDetail } from '../hooks/useApi'

export default function Leads() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [leads, setLeads] = useState([] as LeadDetail[])
  const [total, setTotal] = useState(0)
  const [tier, setTier] = useState('')
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<number[]>([])
  const [detail, setDetail] = useState<LeadDetail | null>(null)

  const fetchLeads = async () => {
    setLoading(true)
    const params: any = { skip: 0, limit: 100 }
    if (tier) params.tier = tier
    if (status) params.status = status
    if (search) params.search = search
    try {
      const r = await api.getLeads(id!, params)
      setLeads(r.data.items)
      setTotal(r.data.total)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchLeads() }, [tier, status, search])

  const toggleSelect = (lid: number) =>
    setSelected(s => s.includes(lid) ? s.filter(x => x !== lid) : [...s, lid])

  const selectAll = () => setSelected(leads.map(l => l.id))
  const clearSelection = () => setSelected([])

  const bulkStatus = async (s: string) => {
    await api.bulkUpdateStatus(id!, selected, s)
    setSelected([])
    fetchLeads()
  }

  const updateStatus = async (lead: LeadDetail, s: string) => {
    await api.updateLead(id!, lead.id, { status: s })
    fetchLeads()
  }

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
        <button className="btn btn-secondary" onClick={() => navigate(`/runs/${id}`)} style={{ marginBottom: 16 }}>← Back to Run</button>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>Leads ({total})</h1>
        <div className="card" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <input className="input" style={{ width: 200 }} placeholder="Search name, city..." value={search} onChange={e => setSearch(e.target.value)} />
          <select className="input" style={{ width: 120 }} value={tier} onChange={e => setTier(e.target.value)}>
            <option value="">All Tiers</option>
            <option value="A">Tier A</option>
            <option value="B">Tier B</option>
            <option value="C">Tier C</option>
          </select>
          <select className="input" style={{ width: 140 }} value={status} onChange={e => setStatus(e.target.value)}>
            <option value="">All Status</option>
            <option value="new">New</option>
            <option value="verified">Verified</option>
            <option value="contacted">Contacted</option>
            <option value="replied">Replied</option>
            <option value="won">Won</option>
            <option value="lost">Lost</option>
            <option value="do_not_contact">Do Not Contact</option>
          </select>
          {selected.length > 0 && (
            <>
              <span className="text-muted text-sm">{selected.length} selected</span>
              <button className="btn btn-secondary" onClick={() => bulkStatus('contacted')}>Mark Contacted</button>
              <button className="btn btn-secondary" onClick={() => bulkStatus('won')}>Mark Won</button>
              <button className="btn btn-secondary" onClick={() => bulkStatus('lost')}>Mark Lost</button>
              <button className="btn btn-danger" onClick={() => bulkStatus('do_not_contact')}>DNC</button>
              <button className="btn btn-secondary" onClick={clearSelection}>Clear</button>
            </>
          )}
        </div>
        {loading ? <p>Loading...</p> : leads.length === 0 ? (
          <div className="card"><p className="text-muted">No leads found.</p></div>
        ) : (
          <div className="card" style={{ overflowX: 'auto' }}>
            <table>
              <thead><tr>
                <th><input type="checkbox" checked={selected.length === leads.length && leads.length > 0} onChange={selected.length === leads.length ? clearSelection : selectAll} /></th>
                <th>Tier</th><th>Business</th><th>Category</th><th>City</th>
                <th>Phone</th><th>Score</th><th>Status</th><th>Channel</th><th></th>
              </tr></thead>
              <tbody>
                {leads.map(lead => (
                  <tr key={lead.id}>
                    <td><input type="checkbox" checked={selected.includes(lead.id)} onChange={() => toggleSelect(lead.id)} /></td>
                    <td><span className={`badge badge-${lead.tier.toLowerCase()}`}>{lead.tier}</span></td>
                    <td><strong>{lead.name}</strong></td>
                    <td>{lead.category}</td>
                    <td>{lead.city}</td>
                    <td>{lead.phone || '—'}</td>
                    <td>{lead.score}</td>
                    <td>
                      <select className="input" style={{ width: 120, padding: '4px 8px' }} value={lead.status} onChange={e => updateStatus(lead, e.target.value)}>
                        <option value="new">New</option>
                        <option value="verified">Verified</option>
                        <option value="contacted">Contacted</option>
                        <option value="replied">Replied</option>
                        <option value="won">Won</option>
                        <option value="lost">Lost</option>
                        <option value="do_not_contact">DNC</option>
                      </select>
                    </td>
                    <td className="text-sm text-muted">{lead.contact_channel}</td>
                    <td><a className="link" href={lead.verify_link} target="_blank" rel="noreferrer">Verify</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {detail && (
          <div className="modal-overlay" onClick={() => setDetail(null)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h3>{detail.name}</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
                <div><strong>Category:</strong> {detail.category}</div>
                <div><strong>City:</strong> {detail.city}</div>
                <div><strong>Phone:</strong> {detail.phone || '—'}</div>
                <div><strong>Email:</strong> {detail.email || '—'}</div>
                <div><strong>Website:</strong> <a href={detail.website} target="_blank" rel="noreferrer">{detail.website || '—'}</a></div>
                <div><strong>Address:</strong> {detail.address || '—'}</div>
                <div><strong>Score:</strong> {detail.score} (Need: {detail.need_score}, Reach: {detail.contact_score}, Budget: {detail.budget_score})</div>
                <div><strong>Status:</strong> {detail.status}</div>
                <div style={{ gridColumn: '1 / -1' }}><strong>Pitch:</strong> {detail.opener}</div>
                {detail.seo_gaps && <div style={{ gridColumn: '1 / -1' }}><strong>SEO Gaps:</strong> {detail.seo_gaps}</div>}
                {detail.compliance_note && <div style={{ gridColumn: '1 / -1', color: '#dc2626', fontSize: 12 }}><strong>Compliance:</strong> {detail.compliance_note}</div>}
              </div>
              <div style={{ marginTop: 16, display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button className="btn btn-secondary" onClick={() => setDetail(null)}>Close</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
