import { useEffect } from 'react'
import { X, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react'
import { useAppStore } from '@/store'

const ICONS = {
  success: <CheckCircle size={16} className="text-green-600" />,
  danger: <AlertCircle size={16} className="text-red-500" />,
  warning: <AlertTriangle size={16} className="text-yellow-500" />,
}

const BG = {
  success: 'border-green-200 bg-green-50',
  danger: 'border-red-200 bg-red-50',
  warning: 'border-yellow-200 bg-yellow-50',
}

function ToastItem({ id, message, type }: { id: number; message: string; type: 'success' | 'danger' | 'warning' }) {
  const dismiss = useAppStore((s) => s.dismissToast)

  useEffect(() => {
    const t = setTimeout(() => dismiss(id), 4000)
    return () => clearTimeout(t)
  }, [id, dismiss])

  return (
    <div className={`flex items-start gap-3 rounded-xl border px-4 py-3 shadow-lg text-sm ${BG[type]}`}>
      {ICONS[type]}
      <span className="flex-1 text-gray-800">{message}</span>
      <button onClick={() => dismiss(id)} className="text-gray-400 hover:text-gray-600 ml-1">
        <X size={14} />
      </button>
    </div>
  )
}

export default function Toast() {
  const toasts = useAppStore((s) => s.toasts)
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 w-80">
      {toasts.map((t) => (
        <ToastItem key={t.id} {...t} />
      ))}
    </div>
  )
}
