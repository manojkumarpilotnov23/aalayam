import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchTemple } from '../api'
import type { TempleDetail } from '../types'

export default function TempleDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [temple, setTemple] = useState<TempleDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showFullText, setShowFullText] = useState(false)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    fetchTemple(id)
      .then(setTemple)
      .catch(() => setError('Temple not found.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-20 text-amber-600 text-lg">Loading…</div>
  if (error || !temple) return (
    <div className="text-center py-20">
      <p className="text-red-500 mb-4">{error}</p>
      <Link to="/" className="text-amber-600 hover:underline">← Back to temples</Link>
    </div>
  )

  const { title, shortDescription, location, content, images, references } = temple
  const { city, district, state } = location.address
  const locationText = [city, district, state].filter(Boolean).join(', ') || 'India'
  const heroImage = images.find(img => img.alt !== 'logo' && !img.url.includes('icons'))

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <header className="bg-white border-b border-amber-100">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Link to="/" className="text-amber-600 hover:underline text-sm">← All Temples</Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Hero */}
        {heroImage && (
          <div className="rounded-2xl overflow-hidden h-64 bg-amber-100">
            <img src={heroImage.url} alt={heroImage.alt || title} className="w-full h-full object-cover" />
          </div>
        )}

        {/* Title & meta */}
        <div className="bg-white rounded-2xl p-6 shadow space-y-3">
          <h1 className="tamil text-2xl font-bold text-gray-900 leading-snug">{title}</h1>
          {shortDescription && (
            <p className="tamil text-gray-600">{shortDescription}</p>
          )}
          <div className="flex flex-wrap gap-2 pt-1">
            <span className="text-sm text-amber-700 bg-amber-50 px-3 py-1 rounded-full">📍 {locationText}</span>
            {location.maps.url && (
              <a
                href={location.maps.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 bg-blue-50 px-3 py-1 rounded-full hover:bg-blue-100"
              >
                🗺 Open in Maps
              </a>
            )}
          </div>
        </div>

        {/* Full text */}
        {content.fullText && (
          <div className="bg-white rounded-2xl p-6 shadow">
            <h2 className="font-semibold text-gray-800 mb-4">தல வரலாறு (Temple History)</h2>
            <div className={`tamil text-gray-700 leading-relaxed text-sm whitespace-pre-line ${!showFullText ? 'line-clamp-6' : ''}`}>
              {content.fullText}
            </div>
            <button
              onClick={() => setShowFullText(v => !v)}
              className="mt-3 text-amber-600 text-sm hover:underline"
            >
              {showFullText ? 'Show less ↑' : 'Read more ↓'}
            </button>
          </div>
        )}

        {/* Nearby temples */}
        {content.nearbyTemples.length > 0 && (
          <div className="bg-white rounded-2xl p-6 shadow">
            <h2 className="font-semibold text-gray-800 mb-4">Nearby Temples</h2>
            <ul className="space-y-3">
              {content.nearbyTemples.map((t, i) => (
                <li key={i} className="flex items-start justify-between gap-4 text-sm">
                  <div>
                    <p className="font-medium text-gray-800">{t.name}</p>
                    <p className="text-gray-500">{t.address}</p>
                  </div>
                  {t.googleMapsUrl && (
                    <a href={t.googleMapsUrl} target="_blank" rel="noopener noreferrer"
                      className="text-blue-500 hover:underline shrink-0">Maps</a>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* References */}
        {references.length > 0 && (
          <div className="bg-white rounded-2xl p-6 shadow">
            <h2 className="font-semibold text-gray-800 mb-3">References</h2>
            <ul className="space-y-1">
              {references.map((r, i) => (
                <li key={i} className="text-sm">
                  {r.url
                    ? <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-amber-600 hover:underline">{r.title}</a>
                    : <span className="text-gray-600">{r.title}</span>
                  }
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  )
}
