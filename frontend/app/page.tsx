'use client'

import { useState, useCallback, useEffect } from 'react'
import { CustomerTable } from '@/components/CustomerTable'
import { UploadCSV } from '@/components/UploadCSV'
import { getCustomers } from '@/lib/api'
import type { Customer } from '@/types'

export default function DashboardPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadCustomers = useCallback(async () => {
    try {
      const data = await getCustomers()
      setCustomers(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load customers')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(loadCustomers)
  }, [loadCustomers])

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Subtle gradient glow at the top */}
      <div className="absolute inset-x-0 top-0 h-96 bg-gradient-to-b from-blue-600/5 via-transparent to-transparent pointer-events-none" />

      <div className="relative max-w-[1400px] mx-auto px-6 py-8">
        {/* Header */}
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
              <span className="text-white text-sm font-bold">C</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              ChurnGuard
            </h1>
            <span className="rounded-full bg-zinc-800 border border-zinc-700 px-2.5 py-0.5 text-xs text-zinc-400">
              beta
            </span>
          </div>
          <p className="text-sm text-zinc-500 max-w-lg">
            AI-powered customer health monitoring. Upload customers, trigger check-in calls, and see risk signals in real time.
          </p>
        </header>

        {/* Upload section */}
        <section className="mb-8">
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-3">
            Import Customers
          </h2>
          <UploadCSV onUploadComplete={loadCustomers} />
        </section>

        {/* Dashboard */}
        <section>
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-3">
            Customer Dashboard
          </h2>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="flex items-center gap-3 text-zinc-500">
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-600 border-t-zinc-300" />
                Loading customers...
              </div>
            </div>
          ) : error ? (
            <div className="rounded-xl bg-red-500/5 border border-red-500/20 p-6 text-center">
              <p className="text-red-400">{error}</p>
              <button
                onClick={loadCustomers}
                className="mt-2 text-sm text-zinc-400 hover:text-zinc-300 underline"
              >
                Retry
              </button>
            </div>
          ) : (
            <CustomerTable initialCustomers={customers} />
          )}
        </section>
      </div>

      {/* Footer */}
      <footer className="border-t border-zinc-900 mt-16">
        <div className="max-w-[1400px] mx-auto px-6 py-6 flex items-center justify-between">
          <p className="text-xs text-zinc-600">
            Built with Bolna AI · ChurnGuard © 2026
          </p>
          <p className="text-xs text-zinc-700">
            Voice AI Customer Success Platform
          </p>
        </div>
      </footer>
    </div>
  )
}
