import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { TempleSummary } from '../types'
import MapModal from './MapModal'

interface Props {
  temple: TempleSummary
  onTagClick?: (tag: string) => void
  activeTags?: string[]
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
}

export default function TempleCard({ temple, onTagClick, activeTags = [] }: Props) {
  const { id, name, templeInfo, reference, location, tags, image } = temple
  const [imgError, setImgError] = useState(false)

  return (
    <Link
      to={`/temples/${encodeURIComponent(id)}`}
      className="block bg-white rounded-2xl shadow hover:shadow-md transition-shadow overflow-hidden group"
    >
      <div className="h-44 bg-amber-50 overflow-hidden">
        {image && !imgError ? (
          <img
            src={image}
            alt={name || id}
            loading="lazy"
            onError={() => setImgError(true)}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-amber-300 text-5xl">
            🛕
          </div>
        )}
      </div>

      <div className="p-4 space-y-2">
        {(name || id) && (
          <p className="tamil text-base font-semibold text-gray-900 leading-snug line-clamp-2">
            {name || id}
          </p>
        )}

        {reference && (
          <p className="text-xs text-amber-700 leading-snug line-clamp-2">{reference}</p>
        )}

        {templeInfo && (
          <p className="tamil text-sm text-gray-600 leading-snug line-clamp-2">{stripHtml(templeInfo)}</p>
        )}

        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {tags.slice(0, 4).map(tag => (
              <button
                key={tag}
                onClick={e => { e.preventDefault(); onTagClick?.(tag) }}
                className={`text-xs px-2 py-0.5 rounded-full transition-colors ${
                  activeTags.includes(tag)
                    ? 'bg-amber-600 text-white'
                    : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                }`}
              >
                {tag}
              </button>
            ))}
            {tags.length > 4 && (
              <span className="text-xs text-gray-400 px-1 py-0.5">+{tags.length - 4}</span>
            )}
          </div>
        )}

        {location && (
          <div className="pt-1">
            <MapModal locationUrl={location} />
          </div>
        )}
      </div>
    </Link>
  )
}
