import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import type { PortfolioChartResponse } from '@/api/types'
import { fmtMonth } from '@/utils/format'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const OPTIONS: ChartOptions<'line'> = {
  responsive: true,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'top' },
    tooltip: {
      callbacks: {
        label: (ctx) =>
          `${ctx.dataset.label}: ${(ctx.parsed.y ?? 0).toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽`,
      },
    },
  },
  scales: {
    y: {
      ticks: {
        callback: (v) => `${Number(v).toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽`,
      },
    },
  },
}

export default function PortfolioChart({ data }: { data: PortfolioChartResponse }) {
  const chartData = {
    labels: data.labels.map(fmtMonth),
    datasets: [
      {
        label: 'Вложено',
        data: data.invested,
        borderColor: '#94a3b8',
        backgroundColor: 'rgba(148,163,184,0.1)',
        fill: true,
        borderDash: [4, 3],
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: 'Без дивидендов',
        data: data.value_no_div,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.08)',
        fill: true,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: 'С дивидендами',
        data: data.value_with_div,
        borderColor: '#16a34a',
        backgroundColor: 'rgba(22,163,74,0.08)',
        fill: true,
        pointRadius: 0,
        tension: 0.3,
      },
    ],
  }

  return <Line data={chartData} options={OPTIONS} />
}
