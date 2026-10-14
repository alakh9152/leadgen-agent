import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface RunSummary {
  id: string
  vertical: string
  market: string
  status: string
  total_leads: number
  tier_a: number
  tier_b: number
  tier_c: number
  error: string | null
  created_at: string
}

export interface LeadItem {
  id: number
  run_id: string
  tier: string
  name: string
  category: string
  city: string
  phone: string
  website: string
  score: number
  status: string
  contact_channel: string
  verify_link: string
}

export interface LeadDetail extends LeadItem {
  address: string
  email: string
  lat: number | null
  lon: number | null
  source: string
  source_url: string
  collected_at: string
  need_score: number
  contact_score: number
  budget_score: number
  why: string
  opener: string
  seo_gaps: string
  compliance_note: string
  country: string
  confidence: number | null
  created_at: string
}

export interface RunRequest {
  vertical: string
  market: string
  sources: string[]
  limit: number
  enrich: boolean
  enrich_cap: number
  country: string
  overture_min_confidence?: number
  weights?: Record<string, number>
  tier_a_need?: number
  tier_a_contact?: number
  exclude_names_csv?: string
}

export interface Stats {
  total_runs: number
  total_leads: number
  tier_a: number
  tier_b: number
  tier_c: number
  contacted: number
  won: number
}

export const api = {
  createRun: (data: RunRequest) => axios.post<RunSummary>(`${API}/api/runs`, data),
  listRuns: () => axios.get<RunSummary[]>(`${API}/api/runs`),
  getRun: (id: string) => axios.get(`${API}/api/runs/${id}`),
  getLeads: (runId: string, params?: { tier?: string; status?: string; search?: string; skip?: number; limit?: number }) =>
    axios.get<{ total: number; items: LeadItem[] }>(`${API}/api/runs/${runId}/leads`, { params }),
  updateLead: (runId: string, leadId: number, patch: Partial<LeadDetail>) =>
    axios.patch<LeadDetail>(`${API}/api/runs/${runId}/leads/${leadId}`, patch),
  bulkUpdateStatus: (runId: string, leadIds: number[], status: string) =>
    axios.put(`${API}/api/runs/${runId}/leads/bulk-status`, { lead_ids: leadIds, status }),
  exportCsv: (runId: string) => `${API}/api/runs/${runId}/export/csv`,
  exportXlsx: (runId: string) => `${API}/api/runs/${runId}/export/xlsx`,
  getStats: () => axios.get<Stats>(`${API}/api/stats`),
  listVerticals: () => axios.get(`${API}/api/verticals`),
}
