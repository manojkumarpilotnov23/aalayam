import { Link } from 'react-router-dom'
import type { TempleSummary } from '../types'

export default function TempleCard({ temple }: { temple: TempleSummary }) {
  const { id, title, shortDescription, location, thumbnail, categories } = temple
  const { city, district, state } = location.address

  const locationText = [city, district, state].filter(Boolean).join(', ') || 'India'

  return (
    <Link
      to={`/temples/${id}`}
      className="block bg-white rounded-2xl shadow hover:shadow-md transition-shadow overflow-hidden group"
    >
      <div className="h-44 bg-amber-50 overflow-hidden">
        {thumbnail ? (
          <img
            src={thumbnail.url}
            alt={thumbnail.alt || title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-amber-300 text-5xl">
            🛕
          </div>
        )}
      </div>

      <div className="p-4 space-y-2">
        <h2 className="tamil font-semibold text-gray-900 leading-snug line-clamp-2">{title}</h2>

        {shortDescription && (
          <p className="tamil text-sm text-gray-500 line-clamp-2">{shortDescription}</p>
        )}

        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">
            📍 {locationText}
          </span>
          {categories[0] && (
            <span className="text-xs text-gray-400">{categories[0]}</span>
          )}
        </div>
      </div>
    </Link>
  )
}
