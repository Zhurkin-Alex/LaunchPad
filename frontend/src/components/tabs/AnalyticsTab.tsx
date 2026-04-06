import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Search, Share2, AlertTriangle } from 'lucide-react'
import { api } from '@/api/client'
import type { TickerAnalysis } from '@/api/types'
import { useAppStore } from '@/store'
import { fmtRub, riskBadgeClass } from '@/utils/format'
import DropZone from '@/components/ui/DropZone'
import SectorBadge from '@/components/ui/SectorBadge'
import Spinner from '@/components/ui/Spinner'
import Tooltip from '@/components/ui/Tooltip'

const RISK_COLS: { key: keyof TickerAnalysis; label: string; hint?: string }[] = [
  { key: 'price', label: 'Цена (₽)', hint: 'Текущая рыночная цена акции по данным MOEX' },
  { key: 'geo_risk_label', label: 'Геориск', hint: 'Геополитический риск: насколько бизнес компании зависит от санкций и внешней политики' },
  { key: 'debt_ebitda', label: 'Долг/EBITDA', hint: 'Долговая нагрузка: отношение чистого долга к прибыли до налогов и амортизации. Норма < 3.0' },
  { key: 'roe_vs_sector', label: 'ROE vs сектор', hint: 'Return on Equity — рентабельность собственного капитала относительно среднего по отрасли' },
  { key: 'dividend_years', label: 'Лет дивидендов', hint: 'Сколько лет подряд компания непрерывно выплачивала дивиденды' },
  { key: 'free_float', label: 'Free-float', hint: 'Доля акций в свободном обращении на бирже (не у крупных акционеров). Чем выше — тем ликвиднее бумага' },
  { key: 'news_sentiment', label: 'Новости', hint: 'Тональность последних новостей о компании: позитивная, нейтральная или негативная' },
]

export default function AnalyticsTab() {
  const { analyzeResult, setAnalyzeResult, showToast } = useAppStore()
  const [tickerText, setTickerText] = useState('')
  const [sessionLink, setSessionLink] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('session')
    if (sid) loadSession(sid)
  }, [])

  async function loadSession(id: string) {
    try {
      const data = await api.getSession(id)
      setAnalyzeResult(data as any)
      setTickerText(data.tickers.join(', '))
    } catch {
      showToast('Сессия не найдена или истекла', 'warning')
    }
  }

  const analyzeMutation = useMutation({
    mutationFn: api.analyze,
    onSuccess: (data) => {
      setAnalyzeResult(data)
      const url = new URL(window.location.href)
      url.searchParams.set('session', data.session_id)
      window.history.replaceState({}, '', url)
      setSessionLink(window.location.href)
    },
    onError: (e: Error) => showToast(e.message, 'danger'),
  })

  const uploadMutation = useMutation({
    mutationFn: api.analyzeFile,
    onSuccess: (data) => {
      setAnalyzeResult(data)
      setTickerText(data.results.map((r) => r.ticker).join(', '))
      showToast('Файл обработан успешно', 'success')
    },
    onError: (e: Error) => showToast(e.message, 'danger'),
  })

  const loading = analyzeMutation.isPending || uploadMutation.isPending

  function handleAnalyze() {
    const tickers = tickerText
      .split(/[,;\s]+/)
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean)
    if (!tickers.length) return showToast('Введите хотя бы один тикер', 'warning')
    analyzeMutation.mutate(tickers)
  }

  function copyLink() {
    navigator.clipboard.writeText(sessionLink)
    showToast('Ссылка скопирована', 'success')
  }

  const { results, portfolio } = analyzeResult ?? {}

  return (
    <div className="space-y-4">
      <div className="card p-6 space-y-4">
        <h2 className="text-base font-bold text-gray-800">Загрузите файл или введите тикеры</h2>
        <DropZone onFile={(f) => uploadMutation.mutate(f)} loading={loading} />
        <div className="flex gap-2">
          <input
            className="input flex-1"
            placeholder="SBER, LKOH, GAZP…"
            value={tickerText}
            onChange={(e) => setTickerText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          />
          <button className="btn-primary" onClick={handleAnalyze} disabled={loading}>
            {loading ? <Spinner size="sm" /> : <Search size={15} />}
            Анализ
          </button>
        </div>
      </div>

      {results && portfolio && (
        <>
          {/* Portfolio summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Акций', value: portfolio.total_count },
              { label: 'Ср. геориск', value: portfolio.avg_risk },
              { label: 'Высокий долг', value: portfolio.high_debt_count },
              { label: 'Рискованный', value: portfolio.riskiest },
            ].map(({ label, value }) => (
              <div key={label} className="card p-4">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-lg font-bold text-gray-900 mt-1">{value}</p>
              </div>
            ))}
          </div>

          {/* Session link */}
          {sessionLink && (
            <div className="card p-3 flex items-center gap-3">
              <Share2 size={15} className="text-gray-400 shrink-0" />
              <input readOnly value={sessionLink} className="input flex-1 text-xs text-gray-500 bg-gray-50" />
              <button className="btn-outline text-xs px-3" onClick={copyLink}>Скопировать</button>
            </div>
          )}

          {/* Results table */}
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="table-head">
                    <th className="px-4 py-3 text-left">Тикер</th>
                    <th className="px-4 py-3 text-left">Компания</th>
                    <th className="px-4 py-3 text-left">Сектор</th>
                    {RISK_COLS.map((c) => (
                      <th key={c.key} className="px-4 py-3 text-left whitespace-nowrap">
                        {c.hint ? <Tooltip text={c.hint}>{c.label}</Tooltip> : c.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr key={r.ticker} className="table-row">
                      <td className="px-4 py-3 font-mono font-bold text-slate-800">{r.ticker}</td>
                      <td className="px-4 py-3 text-gray-700">{r.company}</td>
                      <td className="px-4 py-3"><SectorBadge sector={r.sector} /></td>
                      <td className="px-4 py-3 font-mono">{r.price ? fmtRub(parseFloat(r.price.replace(',', '.'))) : '—'}</td>
                      <td className="px-4 py-3">
                        <span className={`badge ${riskBadgeClass(r.geo_risk_color)}`}>{r.geo_risk_label}</span>
                      </td>
                      <td className="px-4 py-3">{r.debt_ebitda}</td>
                      <td className="px-4 py-3">{r.roe_vs_sector}</td>
                      <td className="px-4 py-3">{r.dividend_years}</td>
                      <td className="px-4 py-3">{r.free_float}</td>
                      <td className="px-4 py-3">{r.news_sentiment}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {results.some((r) => !r.found) && (
            <div className="flex items-center gap-2 text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3">
              <AlertTriangle size={15} />
              Некоторые тикеры не найдены в базе — данные могут быть неполными.
            </div>
          )}
        </>
      )}
    </div>
  )
}
