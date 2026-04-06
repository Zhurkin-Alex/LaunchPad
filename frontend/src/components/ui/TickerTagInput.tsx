import { useState, useRef, type KeyboardEvent } from 'react'
import { X } from 'lucide-react'

interface Props {
  tickers: string[]
  onAdd: (t: string) => void
  onRemove: (t: string) => void
  suggestions?: string[]
  placeholder?: string
}

export default function TickerTagInput({ tickers, onAdd, onRemove, suggestions = [], placeholder }: Props) {
  const [input, setInput] = useState('')
  const [showSug, setShowSug] = useState(false)
  const ref = useRef<HTMLInputElement>(null)

  const filtered = suggestions.filter(
    (s) => s.toLowerCase().startsWith(input.toLowerCase()) && !tickers.includes(s),
  ).slice(0, 8)

  function commit(val: string) {
    const t = val.trim().toUpperCase()
    if (t.length >= 2) onAdd(t)
    setInput('')
    setShowSug(false)
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      commit(input)
    } else if (e.key === 'Backspace' && !input && tickers.length) {
      onRemove(tickers[tickers.length - 1])
    }
  }

  return (
    <div
      className="flex flex-wrap gap-1.5 min-h-[42px] rounded-lg border border-gray-300 px-2 py-1.5 cursor-text focus-within:ring-2 focus-within:ring-slate-500 relative"
      onClick={() => ref.current?.focus()}
    >
      {tickers.map((t) => (
        <span key={t} className="flex items-center gap-1 bg-slate-800 text-white rounded px-2 py-0.5 text-xs font-mono font-bold">
          {t}
          <button type="button" onClick={() => onRemove(t)} className="hover:text-red-300">
            <X size={11} />
          </button>
        </span>
      ))}
      <div className="relative flex-1 min-w-[80px]">
        <input
          ref={ref}
          value={input}
          onChange={(e) => { setInput(e.target.value); setShowSug(true) }}
          onKeyDown={onKey}
          onFocus={() => setShowSug(true)}
          onBlur={() => setTimeout(() => setShowSug(false), 150)}
          placeholder={tickers.length === 0 ? (placeholder ?? 'SBER, LKOH…') : ''}
          className="outline-none bg-transparent text-sm w-full py-0.5"
        />
        {showSug && filtered.length > 0 && (
          <ul className="absolute top-full left-0 z-20 mt-1 w-52 bg-white border border-gray-200 rounded-lg shadow-lg text-sm overflow-hidden">
            {filtered.map((s) => (
              <li
                key={s}
                onMouseDown={() => commit(s)}
                className="px-3 py-1.5 cursor-pointer hover:bg-gray-50 font-mono"
              >
                {s}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
