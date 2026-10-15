import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchTemple } from '../api'
import type { TempleDetail, TempleItem } from '../types'
import MapModal from '../components/MapModal'

function Field({ label, value }: { label: string; value: string }) {
  if (!value) return null
  return (
    <div>
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className="tamil text-sm text-gray-700 leading-relaxed whitespace-pre-line">{value}</p>
    </div>
  )
}

function ItemCard({ item, index }: { item: TempleItem; index: number }) {
  const [expanded, setExpanded] = useState(index === 0)
  const [imgError, setImgError] = useState(false)

  return (
    <div className="bg-white rounded-2xl shadow overflow-hidden">
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-amber-50 transition-colors"
      >
        <span className="tamil text-sm font-medium text-gray-800 line-clamp-2 flex-1 pr-4">
          {item.templeInfo || item.reference || `Entry ${index + 1}`}
        </span>
        <span className="text-amber-500 text-lg shrink-0">{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div className="px-6 pb-6 space-y-4 border-t border-amber-50">
          {item.image && !imgError && (
            <div className="rounded-xl overflow-hidden h-48 mt-4">
              <img
                src={item.image}
                alt=""
                loading="lazy"
                onError={() => setImgError(true)}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          <Field label="Temple Info" value={item.templeInfo} />
          <Field label="Sculptures" value={item.sculptures} />
          <Field label="Inscriptions / கல்வெட்டுகள்" value={item.inscriptions} />
          <Field label="Padhigam / பதிகம்" value={item.padhigam} />

          {item.reference && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">மேலதிக விவரங்களுக்கு</p>
              <p className="tamil text-sm text-gray-600 italic">{item.reference}</p>
            </div>
          )}

          {item.tags.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Tags</p>
              <div className="flex flex-wrap gap-1.5">
                {item.tags.map(tag => (
                  <span
                    key={tag}
                    className="tamil text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {item.location && (
            <MapModal
              locationUrl={item.location}
              className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:underline"
            />
          )}
        </div>
      )}
    </div>
  )
}

export default function TempleDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [temple, setTemple] = useState<TempleDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    setLoading(true)
    fetchTemple(id)
      .then(setTemple)
      .catch(() => setError('Temple not found.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return <div className="flex justify-center py-20 text-amber-600 text-lg">Loading…</div>
  }

  if (error || !temple) {
    return (
      <div className="text-center py-20">
        <p className="text-red-500 mb-4">{error}</p>
        <Link to="/" className="text-amber-600 hover:underline">← Back to temples</Link>
      </div>
    )
  }

  const firstItem = temple.items[0] ?? {}
  const templeName = (firstItem as TempleItem).name || temple.id
  const allTags = Array.from(
    new Set(temple.items.flatMap(item => item.tags))
  )

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <header className="bg-white border-b border-amber-100">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Link to="/" className="text-amber-600 hover:underline text-sm">← All Temples</Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Title card */}
        <div className="bg-white rounded-2xl p-6 shadow space-y-3">
          <h1 className="tamil font-bold text-gray-900 text-xl leading-snug">{templeName}</h1>

          {allTags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {allTags.map(tag => (
                <span
                  key={tag}
                  className="tamil text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {firstItem.location && (
            <MapModal
              locationUrl={firstItem.location as string}
              className="inline-flex items-center gap-1.5 text-sm text-blue-600 bg-blue-50 px-3 py-1 rounded-full hover:bg-blue-100"
            />
          )}

          <p className="text-sm text-gray-500">
            {temple.items.length} entr{temple.items.length === 1 ? 'y' : 'ies'}
          </p>
        </div>

        {/* Items */}
        {temple.items.map((item, i) => (
          <ItemCard key={i} item={item} index={i} />
        ))}
      </main>
    </div>
  )
}
