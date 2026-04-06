import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Hero from '@/components/layout/Hero'
import NavTabs, { type TabId } from '@/components/layout/NavTabs'
import Disclaimer from '@/components/layout/Disclaimer'
import AnalyticsTab from '@/components/tabs/AnalyticsTab'
import DcaTab from '@/components/tabs/DcaTab'
import TopStocksTab from '@/components/tabs/TopStocksTab'
import Toast from '@/components/ui/Toast'

const qc = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 60_000 } } })

function Inner() {
  const [tab, setTab] = useState<TabId>('analytics')

  return (
    <div className="min-h-screen bg-gray-50">
      <Hero />
      <div className="container mx-auto px-4 pb-8">
        <NavTabs active={tab} onChange={setTab} />
        {tab === 'analytics' && <AnalyticsTab />}
        {tab === 'dca' && <DcaTab />}
        {tab === 'top' && <TopStocksTab />}
        <Disclaimer />
      </div>
      <Toast />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Inner />
    </QueryClientProvider>
  )
}
