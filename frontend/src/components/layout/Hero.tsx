import { TrendingUp } from 'lucide-react'

export default function Hero() {
  return (
    <div className="bg-gradient-to-r from-slate-900 to-slate-700 py-8 mb-6">
      <div className="container mx-auto px-4 flex items-center gap-4">
        <div className="p-2.5 bg-white/10 rounded-xl">
          <TrendingUp size={28} className="text-white" />
        </div>
        <div>
          <h1 className="text-white text-2xl font-bold tracking-tight">Анализ Российских Акций</h1>
          <p className="text-white/60 text-sm mt-0.5">
            Анализ портфеля · DCA-калькулятор · Лучшие акции MOEX
          </p>
        </div>
      </div>
    </div>
  )
}
