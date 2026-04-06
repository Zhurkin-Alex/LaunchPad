export interface TickerAnalysis {
  ticker: string
  company: string
  sector: string
  found: boolean
  price: string | null
  price_date: string
  price_is_live: boolean
  geo_risk: number
  geo_risk_label: string
  geo_risk_color: 'success' | 'warning' | 'danger' | 'secondary'
  key_risk: string
  debt_ebitda: string
  roe: string
  roe_vs_sector: string
  roe_color: string
  dividend_years: string
  free_float: string
  news_sentiment: string
}

export interface PortfolioSummary {
  total_count: number
  avg_risk: string
  avg_risk_color: string
  high_debt_count: number
  riskiest: string
}

export interface AnalyzeResponse {
  session_id: string
  results: TickerAnalysis[]
  portfolio: PortfolioSummary
  live_updated_at: string | null
}

export interface DcaPurchase {
  date: string
  price: number
  shares_bought: number
  actual_spent: number
  cumulative_shares: number
  cumulative_invested: number
}

export interface DcaDividendEvent {
  date: string
  value_per_share: number
  shares_held: number
  received: number
  cumulative_div: number
}

export interface DcaSummary {
  total_invested: number
  current_value: number | null
  total_shares: number
  pnl: number | null
  pnl_pct: number | null
  total_dividends: number
  pnl_with_div: number | null
  pnl_pct_with_div: number | null
  dividend_count: number
}

export interface DcaTickerResult {
  ticker: string
  company: string
  sector: string
  error?: string
  purchases: DcaPurchase[]
  dividend_events: DcaDividendEvent[]
  summary: DcaSummary
}

export interface DcaCombined {
  total_invested: number
  total_value: number
  total_dividends: number
  pnl: number | null
  pnl_pct: number | null
  pnl_with_div: number | null
  pnl_pct_with_div: number | null
  ticker_count: number
  valid_count: number
}

export interface DcaResponse {
  results: DcaTickerResult[]
  combined: DcaCombined
}

export interface PortfolioMetrics {
  actual_years: number
  start_price: number
  end_price: number
  total_divs: number
  price_return_pct: number
  price_cagr_pct: number
  total_return_pct: number
  total_cagr_pct: number
  div_yield_pct: number
}

export interface PortfolioEntry {
  ticker: string
  name: string
  sector: string
  weight: number
  metrics: PortfolioMetrics
}

export interface RejectedEntry {
  ticker: string
  name: string
  sector: string
  reason: string
  metrics?: PortfolioMetrics
}

export interface SmartPortfolioParams {
  min_cagr_pct: number
  max_per_sector: number
  max_total: number
  total_analyzed: number
}

export interface SmartPortfolioResponse {
  portfolio: PortfolioEntry[]
  rejected: RejectedEntry[]
  no_data: { ticker: string; name: string; reason: string }[]
  params: SmartPortfolioParams
}

export interface PortfolioChartSummary {
  total_invested: number
  final_value: number
  total_dividends: number
  final_value_with_div: number
  pnl: number
  pnl_pct: number | null
  pnl_with_div: number
  pnl_pct_with_div: number | null
  ticker_count: number
}

export interface PortfolioChartResponse {
  labels: string[]
  invested: number[]
  value_no_div: number[]
  value_with_div: number[]
  summary: PortfolioChartSummary
  error?: string
}

export interface SessionResponse {
  session_id: string
  tickers: string[]
  created_at: string
  results: TickerAnalysis[]
  portfolio: PortfolioSummary
}
