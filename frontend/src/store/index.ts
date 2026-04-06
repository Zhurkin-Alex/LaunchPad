import { create } from 'zustand'
import type { AnalyzeResponse } from '@/api/types'

interface Toast {
  id: number
  message: string
  type: 'success' | 'danger' | 'warning'
}

interface AppStore {
  analyzeResult: AnalyzeResponse | null
  setAnalyzeResult: (r: AnalyzeResponse | null) => void

  dcaTickers: string[]
  addDcaTicker: (t: string) => void
  removeDcaTicker: (t: string) => void

  toasts: Toast[]
  showToast: (message: string, type?: Toast['type']) => void
  dismissToast: (id: number) => void
}

let _toastId = 0

export const useAppStore = create<AppStore>((set) => ({
  analyzeResult: null,
  setAnalyzeResult: (r) => set({ analyzeResult: r }),

  dcaTickers: [],
  addDcaTicker: (t) =>
    set((s) => ({
      dcaTickers: s.dcaTickers.includes(t) ? s.dcaTickers : [...s.dcaTickers, t],
    })),
  removeDcaTicker: (t) =>
    set((s) => ({ dcaTickers: s.dcaTickers.filter((x) => x !== t) })),

  toasts: [],
  showToast: (message, type = 'success') =>
    set((s) => ({ toasts: [...s.toasts, { id: ++_toastId, message, type }] })),
  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))
