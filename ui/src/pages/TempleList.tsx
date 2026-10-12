import { useState, useEffect } from 'react'
import { fetchTemples } from '../api'
import type { TempleSummary } from '../types'
import TempleCard from '../components/TempleCard'

export default function TempleList() {
  const [temples, setTemples] = useState<TempleSummary[]>([])
  const [total, setTotal] = useState(0)
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    fetchTemples(search || undefined)
      .then(data => { setTemples(data.data); setTotal(data.total) })
      .catch(() => setError('Could not load temples. Please try again.'))
      .finally(() => setLoading(false))
  }, [search])

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setSearch(query)
  }

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <header className="bg-white border-b border-amber-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <h1 className="tamil text-2xl font-bold text-amber-800">🛕 ஆலயம் — Aalayam</h1>
          <form onSubmit={handleSearch} className="flex gap-2 w-full sm:w-auto">
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search temples..."
              className="border border-amber-200 rounded-lg px-3 py-1.5 text-sm w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <button
              type="submit"
              className="bg-amber-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-amber-700 transition-colors"
            >
              Search
            </button>
          </form>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {search && (
          <div className="mb-4 flex items-center gap-2 text-sm text-gray-500">
            <span>{total} result{total !== 1 ? 's' : ''} for "<strong>{search}</strong>"</span>
            <button onClick={() => { setSearch(''); setQuery('') }} className="text-amber-600 hover:underline">
              Clear
            </button>
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-20 text-amber-600 text-lg">Loading temples…</div>
        )}

        {error && (
          <div className="text-center py-20 text-red-500">{error}</div>
        )}

        {!loading && !error && temples.length === 0 && (
          <div className="text-center py-20 text-gray-400">No temples found.</div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {temples.map(t => <TempleCard key={t.id} temple={t} />)}
          </div>
        )}
      </main>
    </div>
  )
}
