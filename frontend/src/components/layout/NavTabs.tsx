import { clsx } from 'clsx'
import { BarChart2, Calculator, Star } from 'lucide-react'

export type TabId = 'analytics' | 'dca' | 'top'

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'analytics', label: 'Анализ портфеля', icon: <BarChart2 size={15} /> },
  { id: 'dca', label: 'DCA Калькулятор', icon: <Calculator size={15} /> },
  { id: 'top', label: 'Лучшие акции', icon: <Star size={15} /> },
]

interface Props {
  active: TabId
  onChange: (id: TabId) => void
}

export default function NavTabs({ active, onChange }: Props) {
  return (
    <div className="flex gap-1 mb-6 p-1 bg-white rounded-xl shadow-sm border border-gray-100 w-fit">
      {TABS.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all',
            active === t.id
              ? 'bg-slate-800 text-white shadow'
              : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50',
          )}
        >
          {t.icon}
          {t.label}
        </button>
      ))}
    </div>
  )
}
