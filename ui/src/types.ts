export interface TempleLocation {
  latitude: number | null
  longitude: number | null
  address: {
    city: string | null
    district: string | null
    state: string | null
    country: string
  }
  maps: {
    provider: string | null
    url: string | null
  }
}

export interface TempleImage {
  alt: string
  title: string
  url: string
}

export interface TempleSummary {
  id: string
  title: string
  shortDescription: string
  categories: string[]
  tags: string[]
  location: TempleLocation
  thumbnail: TempleImage | null
}

export interface TempleDetail extends TempleSummary {
  url: string
  content: {
    fullText: string
    timings: {
      days: string[]
      opens: string | null
      closes: string | null
    }[]
    nearbyTemples: {
      name: string
      address: string
      googleMapsUrl: string | null
    }[]
  }
  images: TempleImage[]
  links: { text: string; url: string }[]
  references: { title: string; url: string | null }[]
}

export interface ListResponse {
  total: number
  skip: number
  limit: number
  data: TempleSummary[]
}
