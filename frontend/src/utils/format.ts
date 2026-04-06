export function fmtRub(v: number | null | undefined, decimals = 0): string {
  if (v == null) return '—'
  return (
    v.toLocaleString('ru-RU', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }) + ' ₽'
  )
}

export function fmtPct(v: number | null | undefined, showSign = true): string {
  if (v == null) return '—'
  const sign = showSign && v > 0 ? '+' : ''
  return `${sign}${v.toFixed(1)}%`
}

export function fmtNum(v: number | null | undefined, decimals = 2): string {
  if (v == null) return '—'
  return v.toLocaleString('ru-RU', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function fmtDate(isoStr: string): string {
  const [y, m, d] = isoStr.split('-')
  return `${d}.${m}.${y}`
}

const MONTHS_RU = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

export function fmtMonth(ym: string): string {
  const [y, m] = ym.split('-')
  return `${MONTHS_RU[parseInt(m) - 1]}'${y.slice(2)}`
}

export function pctClass(v: number | null | undefined): string {
  if (v == null) return 'text-gray-400'
  if (v >= 0) return 'text-green-600 font-semibold'
  return 'text-red-500 font-semibold'
}

export function riskBadgeClass(color: string): string {
  switch (color) {
    case 'success': return 'bg-green-100 text-green-800'
    case 'warning': return 'bg-yellow-100 text-yellow-800'
    case 'danger': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-600'
  }
}
