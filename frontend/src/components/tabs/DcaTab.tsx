import { useState, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, TrendingUp } from 'lucide-react'
import { api } from '@/api/client'
import type { DcaTickerResult, DcaPurchase, DcaDividendEvent } from '@/api/types'
import { useAppStore } from '@/store'
import { fmtRub, fmtPct, fmtNum, fmtDate, pctClass } from '@/utils/format'
import TickerTagInput from '@/components/ui/TickerTagInput'
import SectorBadge from '@/components/ui/SectorBadge'
import Spinner from '@/components/ui/Spinner'
import Tooltip from '@/components/ui/Tooltip'

const CURRENT_YEAR = new Date().getFullYear()
const YEARS = Array.from({ length: CURRENT_YEAR - 2009 }, (_, i) => CURRENT_YEAR - 1 - i)

function PurchaseTable({ rows }: { rows: DcaPurchase[] }) {
  const [showAll, setShowAll] = useState(false)
  const visible = showAll ? rows : rows.slice(0, 5)
  return (
    <>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-500 border-b">
            <th className="py-1 text-left">Дата</th>
            <th className="py-1 text-right">Цена</th>
            <th className="py-1 text-right">Куплено</th>
            <th className="py-1 text-right">Потрачено</th>
            <th className="py-1 text-right">Итого акций</th>
            <th className="py-1 text-right">Вложено всего</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((p) => (
            <tr key={p.date} className="border-b border-gray-50">
              <td className="py-1">{fmtDate(p.date)}</td>
              <td className="py-1 text-right font-mono">{fmtRub(p.price)}</td>
              <td className="py-1 text-right">{fmtNum(p.shares_bought)}</td>
              <td className="py-1 text-right font-mono">{fmtRub(p.actual_spent)}</td>
              <td className="py-1 text-right">{fmtNum(p.cumulative_shares)}</td>
              <td className="py-1 text-right font-mono">{fmtRub(p.cumulative_invested)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-1 text-xs text-blue-600 hover:underline flex items-center gap-1"
        >
          {showAll ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          {showAll ? 'Скрыть' : `Показать ещё ${rows.length - 5}`}
        </button>
      )}
    </>
  )
}

function DivTable({ rows }: { rows: DcaDividendEvent[] }) {
  const [showAll, setShowAll] = useState(false)
  const visible = showAll ? rows : rows.slice(0, 5)
  return (
    <>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-500 border-b">
            <th className="py-1 text-left">Дата</th>
            <th className="py-1 text-right">Дивиденд/акц.</th>
            <th className="py-1 text-right">Акций</th>
            <th className="py-1 text-right">Получено</th>
            <th className="py-1 text-right">Всего дивид.</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((d) => (
            <tr key={d.date} className="border-b border-gray-50">
              <td className="py-1">{fmtDate(d.date)}</td>
              <td className="py-1 text-right font-mono">{fmtRub(d.value_per_share, 2)}</td>
              <td className="py-1 text-right">{fmtNum(d.shares_held)}</td>
              <td className="py-1 text-right font-mono">{fmtRub(d.received, 2)}</td>
              <td className="py-1 text-right font-mono">{fmtRub(d.cumulative_div, 2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-1 text-xs text-blue-600 hover:underline flex items-center gap-1"
        >
          {showAll ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          {showAll ? 'Скрыть' : `Показать ещё ${rows.length - 5}`}
        </button>
      )}
    </>
  )
}

function TickerRow({ data }: { data: DcaTickerResult }) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<'purchases' | 'dividends'>('purchases')
  const s = data.summary

  return (
    <>
      <tr
        className="table-row cursor-pointer select-none"
        onClick={() => setOpen(!open)}
      >
        <td className="px-4 py-3">
          {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </td>
        <td className="px-4 py-3 font-mono font-bold text-slate-800">{data.ticker}</td>
        <td className="px-4 py-3 text-gray-700">{data.company}</td>
        <td className="px-4 py-3"><SectorBadge sector={data.sector} /></td>
        <td className="px-4 py-3 font-mono">{fmtRub(s.total_invested)}</td>
        <td className="px-4 py-3 font-mono">{fmtRub(s.current_value)}</td>
        <td className={`px-4 py-3 font-mono ${pctClass(s.pnl)}`}>{fmtRub(s.pnl)}</td>
        <td className={`px-4 py-3 font-semibold ${pctClass(s.pnl_pct)}`}>{fmtPct(s.pnl_pct)}</td>
        <td className="px-4 py-3 font-mono text-green-700">{fmtRub(s.total_dividends, 2)}</td>
        <td className={`px-4 py-3 font-semibold ${pctClass(s.pnl_pct_with_div)}`}>{fmtPct(s.pnl_pct_with_div)}</td>
      </tr>
      {open && (
        <tr>
          <td colSpan={10} className="px-4 py-3 bg-gray-50 border-b">
            <div className="flex gap-2 mb-3">
              <button
                onClick={() => setTab('purchases')}
                className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${tab === 'purchases' ? 'bg-slate-800 text-white' : 'bg-gray-200 text-gray-600 hover:bg-gray-300'}`}
              >
                Покупки ({data.purchases.length})
              </button>
              <button
                onClick={() => setTab('dividends')}
                className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${tab === 'dividends' ? 'bg-slate-800 text-white' : 'bg-gray-200 text-gray-600 hover:bg-gray-300'}`}
              >
                Дивиденды ({data.dividend_events.length})
              </button>
            </div>
            {tab === 'purchases' ? (
              <PurchaseTable rows={data.purchases} />
            ) : (
              <DivTable rows={data.dividend_events} />
            )}
          </td>
        </tr>
      )}
    </>
  )
}

export default function DcaTab() {
  const { dcaTickers, addDcaTicker, removeDcaTicker, showToast } = useAppStore()
  const [startYear, setStartYear] = useState(2020)
  const [amount, setAmount] = useState(10000)
  const [frequency, setFrequency] = useState('monthly')

  const { data: suggestionsData } = useQuery({
    queryKey: ['dca-tickers'],
    queryFn: api.getBacktestTickers,
  })

  const mutation = useMutation({
    mutationFn: api.backtest,
    onError: (e: Error) => showToast(e.message, 'danger'),
  })

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const preload = params.get('tickers')
    if (preload) preload.split(',').forEach((t) => addDcaTicker(t.trim()))
  }, [])

  function calculate() {
    if (!dcaTickers.length) return showToast('Добавьте хотя бы один тикер', 'warning')
    mutation.mutate({ tickers: dcaTickers, start_year: startYear, amount, frequency })
  }

  const { results, combined } = mutation.data ?? {}

  return (
    <div className="space-y-4">
      <div className="card p-6 space-y-4">
        <h2 className="text-base font-bold text-gray-800">DCA-калькулятор</h2>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Тикеры</label>
          <TickerTagInput
            tickers={dcaTickers}
            onAdd={addDcaTicker}
            onRemove={removeDcaTicker}
            suggestions={suggestionsData?.tickers.map((t) => t.ticker) ?? []}
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Год начала</label>
            <select className="select" value={startYear} onChange={(e) => setStartYear(+e.target.value)}>
              {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Сумма закупки (₽)</label>
            <input className="input" type="number" min={1000} step={1000} value={amount}
              onChange={(e) => setAmount(+e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Частота</label>
            <select className="select" value={frequency} onChange={(e) => setFrequency(e.target.value)}>
              <option value="once">Разово</option>
              <option value="monthly">Ежемесячно</option>
              <option value="weekly">Еженедельно</option>
            </select>
          </div>
        </div>
        <button className="btn-primary w-full" onClick={calculate} disabled={mutation.isPending}>
          {mutation.isPending ? <><Spinner size="sm" /> Расчёт…</> : <><TrendingUp size={15} /> Рассчитать</>}
        </button>
      </div>

      {combined && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Вложено', value: fmtRub(combined.total_invested), hint: undefined },
            { label: 'Стоимость', value: fmtRub(combined.total_value), hint: 'Текущая рыночная стоимость всех купленных акций' },
            { label: 'П/У без дивид.', value: fmtPct(combined.pnl_pct), cls: pctClass(combined.pnl_pct), hint: 'Прибыль/Убыток в % от вложенной суммы без учёта дивидендов' },
            { label: 'П/У с дивид.', value: fmtPct(combined.pnl_pct_with_div), cls: pctClass(combined.pnl_pct_with_div), hint: 'Прибыль/Убыток в % с учётом всех полученных дивидендов' },
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

      {results && results.length > 0 && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head">
                  <th className="px-4 py-3 w-6"></th>
                  <th className="px-4 py-3 text-left">Тикер</th>
                  <th className="px-4 py-3 text-left">Компания</th>
                  <th className="px-4 py-3 text-left">Сектор</th>
                  <th className="px-4 py-3 text-left">Вложено</th>
                  <th className="px-4 py-3 text-left"><Tooltip text="Текущая рыночная стоимость всех купленных акций">Стоимость</Tooltip></th>
                  <th className="px-4 py-3 text-left"><Tooltip text="Прибыль или Убыток в рублях: стоимость минус вложенная сумма">П/У</Tooltip></th>
                  <th className="px-4 py-3 text-left"><Tooltip text="Прибыль/Убыток в % от вложенной суммы без дивидендов">П/У %</Tooltip></th>
                  <th className="px-4 py-3 text-left"><Tooltip text="Сумма всех выплаченных дивидендов за период" width={240}>Дивиденды</Tooltip></th>
                  <th className="px-4 py-3 text-left"><Tooltip text="П/У % с учётом всех полученных дивидендов" width={240}>П/У с дивид.</Tooltip></th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <TickerRow key={r.ticker} data={r} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
