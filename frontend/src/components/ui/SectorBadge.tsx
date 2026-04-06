const COLORS: Record<string, string> = {
  'Нефтегаз': 'bg-amber-100 text-amber-800',
  'Финансы': 'bg-blue-100 text-blue-800',
  'Металлы': 'bg-gray-200 text-gray-700',
  'Ритейл': 'bg-pink-100 text-pink-800',
  'Телеком': 'bg-purple-100 text-purple-800',
  'Энергетика': 'bg-yellow-100 text-yellow-800',
  'Транспорт': 'bg-cyan-100 text-cyan-800',
  'IT': 'bg-indigo-100 text-indigo-800',
  'Удобрения': 'bg-green-100 text-green-800',
  'Химия': 'bg-lime-100 text-lime-800',
  'Девелопмент': 'bg-orange-100 text-orange-800',
  'Алмазы': 'bg-sky-100 text-sky-800',
}

export default function SectorBadge({ sector }: { sector: string }) {
  const cls = COLORS[sector] ?? 'bg-gray-100 text-gray-600'
  return <span className={`badge ${cls}`}>{sector}</span>
}
