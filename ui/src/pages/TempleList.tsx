import { useState, useEffect } from 'react'
import { fetchTemples, fetchTags } from '../api'
import type { TempleSummary } from '../types'
import TempleCard from '../components/TempleCard'
import gopuram from '../assets/madurai-gopuram.jpeg'

export default function TempleList() {
  const [temples, setTemples] = useState<TempleSummary[]>([])
  const [total, setTotal] = useState(0)
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [allTags, setAllTags] = useState<string[]>([])
  const [showTagPanel, setShowTagPanel] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchTags().then(setAllTags)
  }, [])

  useEffect(() => {
    setLoading(true)
    setError('')
    fetchTemples(search || undefined, selectedTags.length > 0 ? selectedTags : undefined, 0, 200)
      .then(data => { setTemples(data.data); setTotal(data.total) })
      .catch(() => setError('Could not load temples. Please try again.'))
      .finally(() => setLoading(false))
  }, [search, selectedTags])

  function handleSearch(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSearch(query)
  }

  function toggleTag(tag: string) {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    )
  }

  function clearAll() {
    setSearch('')
    setQuery('')
    setSelectedTags([])
  }

  const hasFilters = search || selectedTags.length > 0

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <header className="bg-white border-b border-amber-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 space-y-3">
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <h1 className="tamil text-2xl font-bold text-amber-800 flex items-center gap-2">
                <img src={gopuram} alt="" className="h-8 w-8 rounded-full object-cover object-top" />
                ஆலயம் — கோயில் கலைக்களஞ்சியம்
              </h1>
            <div className="flex gap-2 w-full sm:w-auto">
              <form onSubmit={handleSearch} className="flex gap-2 flex-1 sm:flex-initial">
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
              <button
                onClick={() => setShowTagPanel(v => !v)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                  selectedTags.length > 0
                    ? 'bg-amber-600 text-white border-amber-600'
                    : 'border-amber-300 text-amber-700 hover:bg-amber-50'
                }`}
              >
                Tags{selectedTags.length > 0 ? ` (${selectedTags.length})` : ''}
              </button>
            </div>
          </div>

          {/* Tag panel */}
          {showTagPanel && allTags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 py-2 border-t border-amber-100 max-h-40 overflow-y-auto">
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`tamil text-xs px-2.5 py-1 rounded-full transition-colors ${
                    selectedTags.includes(tag)
                      ? 'bg-amber-600 text-white'
                      : 'bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          )}

          {/* Active filters summary */}
          {hasFilters && (
            <div className="flex items-center gap-2 text-sm flex-wrap">
              <span className="text-gray-500">
                {total} result{total !== 1 ? 's' : ''}
                {search && <> for "<strong>{search}</strong>"</>}
              </span>
              {selectedTags.map(tag => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full"
                >
                  {tag}
                  <button onClick={() => toggleTag(tag)} className="hover:text-amber-600">×</button>
                </span>
              ))}
              <button onClick={clearAll} className="text-amber-600 hover:underline text-xs ml-1">
                Clear all
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
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
            {temples.map(t => (
              <TempleCard
                key={t.id}
                temple={t}
                onTagClick={toggleTag}
                activeTags={selectedTags}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
