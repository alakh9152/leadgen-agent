import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, RunRequest } from '../hooks/useApi'

interface Props { onClose: () => void }

export default function NewRunModal({ onClose }: Props) {
  const navigate = useNavigate()
  const [verticals, setVerticals] = useState([] as any[])
  const [form, setForm] = useState<RunRequest>({
    vertical: 'web_design_inau',
    market: '',
    sources: ['osm'],
    limit: 300,
    enrich: true,
    enrich_cap: 100,
    country: 'IN',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { api.listVerticals().then(r => setVerticals(r.data)).catch(() => {}) }, [])

  const submit = async () => {
    if (!form.market.trim()) { setError('Market is required'); return }
    setError('')
    setLoading(true)
    try {
      const r = await api.createRun(form)
      onClose()
      navigate(`/runs/${r.data.id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create run')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h3>New Lead Generation Run</h3>
        {error && <div style={{ background: '#fee2e2', color: '#dc2626', padding: 8, borderRadius: 8, fontSize: 13, marginBottom: 12 }}>{error}</div>}
        <div className="form-group">
          <label>Vertical</label>
          <select className="input" value={form.vertical} onChange={e => setForm(f => ({ ...f, vertical: e.target.value }))}>
            {verticals.map(v => <option key={v.key} value={v.key}>{v.label}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Market (city, state, country)</label>
          <input className="input" placeholder="e.g. Jaipur, Rajasthan, India" value={form.market} onChange={e => setForm(f => ({ ...f, market: e.target.value }))} />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Country</label>
            <select className="input" value={form.country} onChange={e => setForm(f => ({ ...f, country: e.target.value }))}>
              <option value="IN">India (IN)</option>
              <option value="AU">Australia (AU)</option>
              <option value="US">United States (US)</option>
            </select>
          </div>
          <div className="form-group">
            <label>Limit</label>
            <input className="input" type="number" value={form.limit} onChange={e => setForm(f => ({ ...f, limit: +e.target.value }))} />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Sources</label>
            <select className="input" multiple value={form.sources} onChange={e => setForm(f => ({ ...f, sources: Array.from(e.currentTarget.selectedOptions, o => o.value) }))}>
              <option value="osm">OpenStreetMap (OSM)</option>
              <option value="overture">Overture Maps</option>
              <option value="localfile">Local File</option>
            </select>
          </div>
          <div className="form-group">
            <label>Enrich Cap</label>
            <input className="input" type="number" value={form.enrich_cap} onChange={e => setForm(f => ({ ...f, enrich_cap: +e.target.value }))} />
          </div>
        </div>
        <div className="form-group">
          <label><input type="checkbox" checked={form.enrich} onChange={e => setForm(f => ({ ...f, enrich: e.target.checked }))} /> Enrich with website data</label>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit} disabled={loading}>
            {loading ? 'Running...' : 'Start Run'}
          </button>
        </div>
      </div>
    </div>
  )
}
