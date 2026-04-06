import { useState, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Info } from 'lucide-react'

interface Props {
  text: string
  children: ReactNode
  width?: number
}

export default function Tooltip({ text, children, width = 220 }: Props) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null)
  const ref = useRef<HTMLSpanElement>(null)

  function show() {
    if (!ref.current) return
    const r = ref.current.getBoundingClientRect()
    setPos({ x: r.left + r.width / 2, y: r.top + window.scrollY })
  }

  function hide() {
    setPos(null)
  }

  return (
    <>
      <span
        ref={ref}
        className="inline-flex items-center gap-1 cursor-default"
        onMouseEnter={show}
        onMouseLeave={hide}
      >
        <span className="border-b border-dashed border-gray-400 leading-tight">
          {children}
        </span>
        <Info size={11} className="text-gray-400 shrink-0" />
      </span>

      {pos && createPortal(
        <div
          style={{
            position: 'absolute',
            left: pos.x,
            top: pos.y - 10,
            transform: 'translate(-50%, -100%)',
            width,
            zIndex: 9999,
          }}
          className="rounded-lg bg-gray-900 text-white text-xs leading-relaxed px-3 py-2 shadow-xl pointer-events-none font-normal normal-case tracking-normal"
        >
          {text}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-gray-900" />
        </div>,
        document.body,
      )}
    </>
  )
}
