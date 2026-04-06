import { useCallback, useState } from 'react'
import { Upload } from 'lucide-react'

interface Props {
  onFile: (file: File) => void
  loading?: boolean
}

export default function DropZone({ onFile, loading }: Props) {
  const [over, setOver] = useState(false)

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setOver(false)
      const file = e.dataTransfer.files[0]
      if (file) onFile(file)
    },
    [onFile],
  )

  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setOver(true) }}
      onDragLeave={() => setOver(false)}
      onDrop={handleDrop}
      className={`flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 cursor-pointer transition-colors
        ${over ? 'border-slate-600 bg-slate-50' : 'border-gray-300 hover:border-slate-400 hover:bg-gray-50'}`}
    >
      <Upload size={28} className="text-gray-400" />
      <p className="text-sm text-gray-500 text-center">
        Перетащите PDF или изображение сюда
        <br />
        <span className="text-xs text-gray-400">или нажмите для выбора файла</span>
      </p>
      <input
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        className="hidden"
        disabled={loading}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f) }}
      />
    </label>
  )
}
