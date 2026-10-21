import { useState, useEffect } from 'react'
import { fetchAllTemples, fetchTemple, updateTemple } from '../api'
import type { TempleSummary } from '../types'
import ContentEditor from '../components/ContentEditor'

const RICH_FIELDS = ['templeInfo', 'sculptures', 'inscriptions', 'padhigam'] as const
type RichField = (typeof RICH_FIELDS)[number]

const PLAIN_FIELDS = ['name', 'location', 'image', 'reference'] as const
type PlainField = (typeof PLAIN_FIELDS)[number]

type FormState = Record<RichField | PlainField | 'tags', string>

const EMPTY: FormState = {
  name: '', location: '', image: '', reference: '',
  templeInfo: '', sculptures: '', inscriptions: '', padhigam: '', tags: '',
}

const LABELS: Record<keyof FormState, string> = {
  name: 'Temple Name', location: 'Location', image: 'Image URL',
  reference: 'Reference', templeInfo: 'Temple Info', sculptures: 'Sculptures',
  inscriptions: 'Inscriptions', padhigam: 'Padhigam', tags: 'Tags (comma-separated)',
}

export default function EditPage() {
  const [temples, setTemples] = useState<TempleSummary[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [form, setForm] = useState<FormState>(EMPTY)
  const [status, setStatus] = useState<'idle' | 'loading' | 'saving' | 'saved' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    fetchAllTemples()
      .then(r => setTemples(r.data))
      .catch(() => setErrorMsg('Could not load temple list.'))
  }, [])

  async function handleSelect(id: string) {
    setSelectedId(id)
    if (!id) { setForm(EMPTY); return }
    setStatus('loading')
    try {
      const detail = await fetchTemple(id)
      const item = detail.items?.[0] ?? {}
      setForm({
        name: item.name ?? '',
        location: item.location ?? '',
        image: item.image ?? '',
        reference: item.reference ?? '',
        templeInfo: item.templeInfo ?? '',
        sculptures: item.sculptures ?? '',
        inscriptions: item.inscriptions ?? '',
        padhigam: item.padhigam ?? '',
        tags: Array.isArray(item.tags) ? item.tags.join(', ') : (item.tags ?? ''),
      })
      setStatus('idle')
    } catch {
      setErrorMsg('Could not load temple.')
      setStatus('error')
    }
  }

  function setPlain(field: PlainField | 'tags', value: string) {
    setForm(f => ({ ...f, [field]: value }))
  }

  function setRich(field: RichField, html: string) {
    setForm(f => ({ ...f, [field]: html }))
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedId) return
    setStatus('saving')
    setErrorMsg('')
    try {
      await updateTemple(selectedId, { ...form })
      setStatus('saved')
      setTimeout(() => setStatus('idle'), 2500)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Save failed')
      setStatus('error')
    }
  }

  return (
    <div className="min-h-screen bg-amber-50">
      <header className="bg-white border-b border-amber-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-4">
          <a href="#/" className="text-amber-700 hover:underline text-sm">← Back</a>
          <h1 className="tamil text-xl font-bold text-amber-800">Edit Temple</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Temple selector */}
        <div>
          <label className="block text-sm font-medium text-amber-900 mb-1">Select Temple</label>
          <select
            value={selectedId}
            onChange={e => handleSelect(e.target.value)}
            className="w-full border border-amber-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
          >
            <option value="">— choose a temple —</option>
            {temples.map(t => (
              <option key={t.id} value={t.id}>{t.name || t.id}</option>
            ))}
          </select>
        </div>

        {status === 'loading' && (
          <div className="text-amber-600 text-sm">Loading temple data…</div>
        )}

        {selectedId && status !== 'loading' && (
          <form onSubmit={handleSave} className="space-y-5">
            {/* Plain text fields */}
            {PLAIN_FIELDS.map(field => (
              <div key={field}>
                <label className="block text-sm font-medium text-amber-900 mb-1">{LABELS[field]}</label>
                <input
                  type="text"
                  value={form[field]}
                  onChange={e => setPlain(field, e.target.value)}
                  className="w-full border border-amber-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>
            ))}

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-amber-900 mb-1">{LABELS.tags}</label>
              <input
                type="text"
                value={form.tags}
                onChange={e => setPlain('tags', e.target.value)}
                placeholder="Shiva, Chola, Rock-cut"
                className="w-full border border-amber-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
            </div>

            {/* Rich text fields */}
            {RICH_FIELDS.map(field => (
              <div key={field}>
                <label className="block text-sm font-medium text-amber-900 mb-1">{LABELS[field]}</label>
                <ContentEditor
                  value={form[field]}
                  onChange={html => setRich(field, html)}
                  placeholder={`Enter ${LABELS[field].toLowerCase()}…`}
                />
              </div>
            ))}

            {/* Status / Save */}
            <div className="flex items-center gap-4 pt-2">
              <button
                type="submit"
                disabled={status === 'saving'}
                className="bg-amber-600 text-white px-6 py-2 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50"
              >
                {status === 'saving' ? 'Saving…' : 'Save'}
              </button>
              {status === 'saved' && <span className="text-green-600 text-sm">Saved successfully.</span>}
              {status === 'error' && <span className="text-red-500 text-sm">{errorMsg}</span>}
            </div>
          </form>
        )}

        {!selectedId && errorMsg && (
          <div className="text-red-500 text-sm">{errorMsg}</div>
        )}
      </main>
    </div>
  )
}
