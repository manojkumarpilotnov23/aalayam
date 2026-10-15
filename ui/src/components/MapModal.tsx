import { useState, useRef } from 'react'
import { fetchMapEmbed } from '../api'

interface Props {
  locationUrl: string
  className?: string
}

export default function MapModal({ locationUrl, className }: Props) {
  const [open, setOpen] = useState(false)
  const [embedUrl, setEmbedUrl] = useState<string | null>(null)
  const [fetching, setFetching] = useState(false)
  const [fetchError, setFetchError] = useState(false)
  const fetched = useRef(false)

  async function handleOpen(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    setOpen(true)
    if (fetched.current) return
    fetched.current = true
    setFetching(true)
    const url = await fetchMapEmbed(locationUrl)
    setEmbedUrl(url)
    setFetchError(url === null)
    setFetching(false)
  }

  function handleClose() {
    setOpen(false)
  }

  return (
    <>
      <button
        onClick={handleOpen}
        className={className ?? 'inline-flex items-center gap-1 text-xs text-blue-600 hover:underline'}
      >
        🗺 View Map
      </button>

      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-4"
          onClick={handleClose}
        >
          <div
            className="bg-white rounded-2xl overflow-hidden w-full max-w-2xl shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100">
              <span className="font-semibold text-sm text-gray-700">Location</span>
              <button
                onClick={handleClose}
                className="text-gray-400 hover:text-gray-700 text-2xl leading-none"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <div className="h-80">
              {fetching && (
                <div className="h-full flex items-center justify-center text-amber-600 text-sm">
                  Loading map…
                </div>
              )}

              {!fetching && fetchError && (
                <div className="h-full flex flex-col items-center justify-center gap-3 text-gray-400 text-sm">
                  <span>Map unavailable.</span>
                  <a
                    href={locationUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:underline"
                  >
                    Open in Google Maps ↗
                  </a>
                </div>
              )}

              {!fetching && embedUrl && (
                <iframe
                  src={embedUrl}
                  title="Temple location"
                  className="w-full h-full border-0"
                  allowFullScreen
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
