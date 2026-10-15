import { API_BASE } from './config'
import type { ListResponse, TempleDetail } from './types'

export async function fetchTemples(
  q?: string,
  tags?: string[],
  skip = 0,
  limit = 20,
): Promise<ListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
  if (q) params.set('q', q)
  if (tags && tags.length > 0) params.set('tags', tags.join(','))
  const res = await fetch(`${API_BASE}/temples?${params}`)
  if (!res.ok) throw new Error('Failed to fetch temples')
  return res.json()
}

export async function fetchTemple(id: string): Promise<TempleDetail> {
  const res = await fetch(`${API_BASE}/temples/${encodeURIComponent(id)}`)
  if (!res.ok) throw new Error('Temple not found')
  return res.json()
}

export async function fetchTags(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/tags`)
  if (!res.ok) return []
  const data = await res.json()
  return data.tags ?? []
}

export async function fetchMapEmbed(locationUrl: string): Promise<string | null> {
  const res = await fetch(`${API_BASE}/maps/embed?url=${encodeURIComponent(locationUrl)}`)
  if (!res.ok) return null
  const data = await res.json()
  return data.embedUrl ?? null
}
