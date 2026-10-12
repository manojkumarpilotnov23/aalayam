import { API_BASE } from './config'
import type { ListResponse, TempleDetail } from './types'

export async function fetchTemples(q?: string, skip = 0, limit = 20): Promise<ListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
  if (q) params.set('q', q)
  const res = await fetch(`${API_BASE}/temples?${params}`)
  if (!res.ok) throw new Error('Failed to fetch temples')
  return res.json()
}

export async function fetchTemple(id: string): Promise<TempleDetail> {
  const res = await fetch(`${API_BASE}/temples/${id}`)
  if (!res.ok) throw new Error('Temple not found')
  return res.json()
}
