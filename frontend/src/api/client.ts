import type {
  AnalyzeResponse,
  DcaResponse,
  PortfolioChartResponse,
  SessionResponse,
  SmartPortfolioResponse,
} from './types'

const BASE = ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  analyze(tickers: string[]): Promise<AnalyzeResponse> {
    return request('/api/analyze', {
      method: 'POST',
      body: JSON.stringify({ tickers }),
    })
  },

  analyzeFile(file: File): Promise<AnalyzeResponse> {
    const form = new FormData()
    form.append('file', file)
    return fetch('/api/upload', { method: 'POST', body: form }).then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.json()
    })
  },

  getSession(id: string): Promise<SessionResponse> {
    return request(`/api/session/${id}`)
  },

  backtest(params: {
    tickers: string[]
    start_year: number
    amount: number
    frequency: string
  }): Promise<DcaResponse> {
    return request('/api/backtest', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  },

  getBacktestTickers(): Promise<{ tickers: string[] }> {
    return request('/api/backtest/tickers')
  },

  smartPortfolio(years: number, minCagr: number): Promise<SmartPortfolioResponse> {
    return request(`/api/smart-portfolio?years=${years}&min_cagr=${minCagr}`)
  },

  portfolioChart(params: {
    tickers: string[]
    weights: number[]
    start_year: number
    amount: number
    frequency: string
  }): Promise<PortfolioChartResponse> {
    return request('/api/portfolio-chart', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  },
}
