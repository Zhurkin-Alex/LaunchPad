import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { RefreshCw, ChevronDown, ChevronRight, TrendingUp } from 'lucide-react'
import { api } from '@/api/client'
import type { PortfolioEntry, RejectedEntry, SmartPortfolioResponse } from '@/api/types'
import { useAppStore } from '@/store'
import { fmtPct, fmtRub, pctClass } from '@/utils/format'
import SectorBadge from '@/components/ui/SectorBadge'
import Spinner from '@/components/ui/Spinner'
import PortfolioChart from '@/components/charts/PortfolioChart'
import Tooltip from '@/components/ui/Tooltip'
import type { PortfolioChartResponse } from '@/api/types'

const CURRENT_YEAR = new Date().getFullYear()
const YEARS = Array.from({ length: CURRENT_YEAR - 2009 }, (_, i) => CURRENT_YEAR - 1 - i)

function PortfolioTable({ rows }: { rows: PortfolioEntry[] }) {
  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
              <tr className="table-head">
              <th className="px-4 py-3 text-left">
                <Tooltip text="Рекомендуемая доля в портфеле, пропорциональна суммарному CAGR">Доля</Tooltip>
              </th>
              <th className="px-4 py-3 text-left">Тикер</th>
              <th className="px-4 py-3 text-left">Компания</th>
              <th className="px-4 py-3 text-left">Сектор</th>
              <th className="px-4 py-3 text-right">
                <Tooltip text="CAGR цены — среднегодовой темп роста стоимости акции (без дивидендов)" width={260}>CAGR цены</Tooltip>
              </th>
              <th className="px-4 py-3 text-right">
                <Tooltip text="Среднегодовая дивидендная доходность за весь период анализа" width={260}>Дивид./год</Tooltip>
              </th>
              <th className="px-4 py-3 text-right">
                <Tooltip text="CAGR суммарный — среднегодовая доходность с учётом роста цены и дивидендов вместе" width={280}>CAGR сумм.</Tooltip>
              </th>
              <th className="px-4 py-3 text-right">
                <Tooltip text="Количество лет исторических данных MOEX, использованных в расчёте" width={240}>Лет данных</Tooltip>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.ticker} className="table-row">
                <td className="px-4 py-3 font-semibold text-gray-700">{r.weight.toFixed(0)}%</td>
                <td className="px-4 py-3 font-mono font-bold text-slate-800">{r.ticker}</td>
                <td className="px-4 py-3 text-gray-700">{r.name}</td>
                <td className="px-4 py-3"><SectorBadge sector={r.sector} /></td>
                <td className={`px-4 py-3 text-right ${pctClass(r.metrics.price_cagr_pct)}`}>{fmtPct(r.metrics.price_cagr_pct)}</td>
                <td className="px-4 py-3 text-right text-green-700">{fmtPct(r.metrics.div_yield_pct)}</td>
                <td className={`px-4 py-3 text-right font-bold ${pctClass(r.metrics.total_cagr_pct)}`}>{fmtPct(r.metrics.total_cagr_pct)}</td>
                <td className="px-4 py-3 text-right text-gray-500">{r.metrics.actual_years.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function RejectedSection({ rows }: { rows: RejectedEntry[] }) {
  const [open, setOpen] = useState(false)
  if (!rows.length) return null
  return (
    <div className="card overflow-hidden">
      <button
        className="w-full flex items-center gap-2 px-5 py-3 text-sm font-semibold text-gray-600 hover:bg-gray-50"
        onClick={() => setOpen(!open)}
      >
        {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        Не прошли фильтр ({rows.length})
      </button>
      {open && (
        <div className="overflow-x-auto border-t">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head">
                <th className="px-4 py-2 text-left">Тикер</th>
                <th className="px-4 py-2 text-left">Компания</th>
                <th className="px-4 py-2 text-left">Сектор</th>
                <th className="px-4 py-2 text-left">Причина</th>
                <th className="px-4 py-2 text-right">CAGR сумм.</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.ticker} className="table-row">
                  <td className="px-4 py-2 font-mono font-bold">{r.ticker}</td>
                  <td className="px-4 py-2 text-gray-600">{r.name}</td>
                  <td className="px-4 py-2"><SectorBadge sector={r.sector} /></td>
                  <td className="px-4 py-2 text-red-600 text-xs">{r.reason}</td>
                  <td className={`px-4 py-2 text-right ${pctClass(r.metrics?.total_cagr_pct)}`}>
                    {r.metrics ? fmtPct(r.metrics.total_cagr_pct) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function TopStocksTab() {
  const { showToast } = useAppStore()
  const [years, setYears] = useState(5)
  const [minCagr, setMinCagr] = useState(12)
  const [portfolio, setPortfolio] = useState<SmartPortfolioResponse | null>(null)

  // chart state
  const [chartYear, setChartYear] = useState(2020)
  const [chartAmount, setChartAmount] = useState(10000)
  const [chartFreq, setChartFreq] = useState('monthly')
  const [chartData, setChartData] = useState<PortfolioChartResponse | null>(null)

  const loadMutation = useMutation({
    mutationFn: () => api.smartPortfolio(years, minCagr),
    onSuccess: (data) => setPortfolio(data),
    onError: (e: Error) => showToast(e.message, 'danger'),
  })

  const chartMutation = useMutation({
    mutationFn: () => {
      if (!portfolio?.portfolio.length) throw new Error('Сначала загрузите портфель')
      return api.portfolioChart({
        tickers: portfolio.portfolio.map((p) => p.ticker),
        weights: portfolio.portfolio.map((p) => p.weight / 100),
        start_year: chartYear,
        amount: chartAmount,
        frequency: chartFreq,
      })
    },
    onSuccess: (data) => setChartData(data),
    onError: (e: Error) => showToast(e.message, 'danger'),
  })

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="card p-6 space-y-4">
        <h2 className="text-base font-bold text-gray-800">Умная подборка акций MOEX</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Горизонт анализа</label>
            <select className="select" value={years} onChange={(e) => setYears(+e.target.value)}>
              <option value={3}>3 года</option>
              <option value={5}>5 лет</option>
              <option value={10}>10 лет</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Мин. CAGR (%)</label>
            <input
              className="input"
              type="number"
              min={0}
              max={50}
              step={1}
              value={minCagr}
              onChange={(e) => setMinCagr(+e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <button
              className="btn-primary w-full"
              onClick={() => loadMutation.mutate()}
              disabled={loadMutation.isPending}
            >
              {loadMutation.isPending ? <><Spinner size="sm" /> Анализируем…</> : <><RefreshCw size={15} /> Обновить подборку</>}
            </button>
          </div>
        </div>
        {loadMutation.isPending && (
          <p className="text-xs text-gray-500 italic">
            ⏳ Запрашиваем данные по всем акциям MOEX, это может занять 20–60 секунд…
          </p>
        )}
      </div>

      {portfolio && (
        <>
          <div className="flex items-center gap-3 text-sm text-gray-600 px-1">
            <span>Проанализировано: <b>{portfolio.params.total_analyzed}</b></span>
            <span>·</span>
            <span>В портфеле: <b>{portfolio.portfolio.length}</b></span>
            <span>·</span>
            <span>Мин. CAGR: <b>{portfolio.params.min_cagr_pct}%</b></span>
          </div>
          <PortfolioTable rows={portfolio.portfolio} />
          <RejectedSection rows={portfolio.rejected} />

          {/* Simulator */}
          <div className="card p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-800">Симулятор доходности</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Год начала</label>
                <select className="select" value={chartYear} onChange={(e) => setChartYear(+e.target.value)}>
                  {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Сумма закупки (₽)</label>
                <input className="input" type="number" min={1000} step={1000} value={chartAmount}
                  onChange={(e) => setChartAmount(+e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Частота</label>
                <select className="select" value={chartFreq} onChange={(e) => setChartFreq(e.target.value)}>
                  <option value="once">Разово</option>
                  <option value="monthly">Ежемесячно</option>
                  <option value="weekly">Еженедельно</option>
                </select>
              </div>
            </div>
            <button className="btn-primary" onClick={() => chartMutation.mutate()} disabled={chartMutation.isPending}>
              {chartMutation.isPending ? <><Spinner size="sm" /> Расчёт…</> : <><TrendingUp size={15} /> Построить график</>}
            </button>
          </div>

          {chartData && (
            <>
              {chartData.summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label: 'Вложено', value: fmtRub(chartData.summary.total_invested), hint: undefined },
                    { label: 'Стоимость', value: fmtRub(chartData.summary.final_value), hint: 'Итоговая стоимость портфеля по последним ценам MOEX' },
                    { label: 'П/У без дивид.', value: fmtPct(chartData.summary.pnl_pct), cls: pctClass(chartData.summary.pnl_pct), hint: 'Прибыль/Убыток в % только от роста цены акций' },
                    { label: 'П/У с дивид.', value: fmtPct(chartData.summary.pnl_pct_with_div), cls: pctClass(chartData.summary.pnl_pct_with_div), hint: 'Прибыль/Убыток в % с учётом всех полученных дивидендов' },
                  ].map(({ label, value, cls, hint }) => (
                    <div key={label} className="card p-4">
                      <p className="text-xs text-gray-500">
                        {hint ? <Tooltip text={hint} width={260}>{label}</Tooltip> : label}
                      </p>
                      <p className={`text-lg font-bold mt-1 ${cls ?? 'text-gray-900'}`}>{value}</p>
                    </div>
                  ))}
                </div>
              )}
              <div className="card p-5">
                <PortfolioChart data={chartData} />
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
