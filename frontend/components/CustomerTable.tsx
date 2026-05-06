'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { HealthScoreBadge } from './HealthScoreBadge'
import { CallStatusBadge } from './CallStatusBadge'
import { TranscriptModal } from './TranscriptModal'
import { supabase } from '@/lib/supabase'
import { triggerCampaign, getCustomers } from '@/lib/api'
import type { Customer, CallResult } from '@/types'

interface CustomerTableProps {
  initialCustomers: Customer[]
}

export function CustomerTable({ initialCustomers }: CustomerTableProps) {
  const [customers, setCustomers] = useState<Customer[]>(initialCustomers)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [isTriggering, setIsTriggering] = useState(false)
  const [triggerMessage, setTriggerMessage] = useState<string | null>(null)

  // Refresh customers from the API
  const refreshCustomers = useCallback(async () => {
    try {
      const data = await getCustomers()
      setCustomers(data)
    } catch (err) {
      console.error('Failed to refresh customers:', err)
    }
  }, [])

  // Supabase Realtime subscription
  useEffect(() => {
    const channel = supabase
      .channel('call_results_changes')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'call_results' },
        (payload) => {
          const newResult = payload.new as CallResult
          setCustomers(prev =>
            prev.map(c =>
              c.id === newResult.customer_id
                ? { ...c, status: 'completed' as const, call_result: newResult }
                : c
            )
          )
        }
      )
      .on(
        'postgres_changes',
        { event: 'UPDATE', schema: 'public', table: 'customers' },
        (payload) => {
          const updated = payload.new as Partial<Customer> & { id: string }
          setCustomers(prev =>
            prev.map(c =>
              c.id === updated.id
                ? { ...c, ...updated }
                : c
            )
          )
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  // Trigger campaign for pending customers
  const handleTriggerCampaign = useCallback(async () => {
    const pendingIds = customers
      .filter(c => c.status === 'pending' || c.status === 'failed')
      .map(c => c.id)

    if (pendingIds.length === 0) {
      setTriggerMessage('No pending customers to call')
      return
    }

    setIsTriggering(true)
    setTriggerMessage(null)

    try {
      const result = await triggerCampaign(pendingIds)
      setTriggerMessage(`${result.triggered} call${result.triggered !== 1 ? 's' : ''} triggered`)
      await refreshCustomers()
    } catch (err) {
      setTriggerMessage(err instanceof Error ? err.message : 'Failed to trigger')
    } finally {
      setIsTriggering(false)
    }
  }, [customers, refreshCustomers])

  // Summary stats
  const stats = {
    total: customers.length,
    healthy: customers.filter(c => c.call_result?.risk_label === 'Healthy').length,
    monitor: customers.filter(c => c.call_result?.risk_label === 'Monitor').length,
    atRisk: customers.filter(c => c.call_result?.risk_label === 'At-Risk').length,
    pending: customers.filter(c => !c.call_result && c.status !== 'failed').length,
  }

  const riskColor: Record<string, string> = {
    'Healthy': 'text-emerald-400',
    'Monitor': 'text-amber-400',
    'At-Risk': 'text-red-400',
  }

  return (
    <div className="space-y-6">
      {/* Header with stats and action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex flex-wrap gap-3">
          <StatCard label="Total" value={stats.total} color="text-zinc-200" />
          <StatCard label="Healthy" value={stats.healthy} color="text-emerald-400" />
          <StatCard label="Monitor" value={stats.monitor} color="text-amber-400" />
          <StatCard label="At-Risk" value={stats.atRisk} color="text-red-400" />
          <StatCard label="Pending" value={stats.pending} color="text-zinc-500" />
        </div>
        <div className="flex items-center gap-3">
          {triggerMessage && (
            <span className="text-sm text-zinc-400">{triggerMessage}</span>
          )}
          <Button
            onClick={handleTriggerCampaign}
            disabled={isTriggering || customers.length === 0}
            className="bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            {isTriggering ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Calling...
              </span>
            ) : (
              '🚀 Start Campaign'
            )}
          </Button>
        </div>
      </div>

      {/* Customer table */}
      <Card className="bg-zinc-900/50 border-zinc-800 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400 font-medium">Name</TableHead>
              <TableHead className="text-zinc-400 font-medium">Company</TableHead>
              <TableHead className="text-zinc-400 font-medium">Day</TableHead>
              <TableHead className="text-zinc-400 font-medium">Status</TableHead>
              <TableHead className="text-zinc-400 font-medium">Score</TableHead>
              <TableHead className="text-zinc-400 font-medium">Risk</TableHead>
              <TableHead className="text-zinc-400 font-medium">Blocker</TableHead>
              <TableHead className="text-zinc-400 font-medium text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {customers.length === 0 ? (
              <TableRow className="border-zinc-800">
                <TableCell colSpan={8} className="text-center text-zinc-500 py-12">
                  No customers yet. Upload a CSV to get started.
                </TableCell>
              </TableRow>
            ) : (
              customers.map((customer) => (
                <TableRow
                  key={customer.id}
                  className="border-zinc-800 hover:bg-zinc-800/30 transition-colors"
                >
                  <TableCell>
                    <div>
                      <p className="font-medium text-zinc-200">{customer.name}</p>
                      <p className="text-xs text-zinc-500">{customer.email}</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-zinc-400 text-sm">
                    {customer.company || '—'}
                  </TableCell>
                  <TableCell className="text-zinc-400 text-sm">
                    {customer.days_since_signup ? `D${customer.days_since_signup}` : '—'}
                  </TableCell>
                  <TableCell>
                    <CallStatusBadge status={customer.status} />
                  </TableCell>
                  <TableCell>
                    <HealthScoreBadge score={customer.call_result?.health_score ?? null} />
                  </TableCell>
                  <TableCell>
                    {customer.call_result?.risk_label ? (
                      <span className={`text-sm font-medium ${riskColor[customer.call_result.risk_label] || 'text-zinc-400'}`}>
                        {customer.call_result.risk_label}
                      </span>
                    ) : (
                      <span className="text-sm text-zinc-600">—</span>
                    )}
                  </TableCell>
                  <TableCell className="max-w-[200px]">
                    <p className="text-sm text-zinc-400 truncate">
                      {customer.call_result?.key_blocker || '—'}
                    </p>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {customer.call_result?.transcript && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                          onClick={() => setSelectedCustomer(customer)}
                        >
                          View
                        </Button>
                      )}
                      {customer.call_result?.recommendation === 'escalate' && (
                        <Badge className="bg-red-500/15 text-red-400 border border-red-500/30 text-xs">
                          Escalate
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Transcript modal */}
      <TranscriptModal
        callResult={selectedCustomer?.call_result ?? null}
        customerName={selectedCustomer?.name ?? ''}
        open={!!selectedCustomer}
        onClose={() => setSelectedCustomer(null)}
      />
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-zinc-900/50 border border-zinc-800 px-3 py-2">
      <span className={`text-lg font-bold ${color}`}>{value}</span>
      <span className="text-xs text-zinc-500 uppercase tracking-wider">{label}</span>
    </div>
  )
}
