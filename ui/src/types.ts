export interface TempleItem {
  id: string
  name: string
  reference: string
  location: string
  padhigam: string
  templeInfo: string
  sculptures: string
  inscriptions: string
  tags: string[]
  image: string | null
}

export interface TempleSummary {
  id: string
  name: string
  templeInfo: string
  reference: string
  location: string
  tags: string[]
  image: string | null
  itemCount: number
}

export interface TempleDetail {
  id: string
  items: TempleItem[]
}

export interface ListResponse {
  total: number
  skip: number
  limit: number
  data: TempleSummary[]
}
