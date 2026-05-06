'use client'

import type { CustomerStatus } from '@/types'

interface CallStatusBadgeProps {
  status: CustomerStatus
}

const STATUS_CONFIG: Record<CustomerStatus, { color: string; label: string; pulse: boolean }> = {
  pending: { color: 'bg-zinc-500', label: 'Pending', pulse: false },
  scheduled: { color: 'bg-blue-500', label: 'Scheduled', pulse: false },
  in_call: { color: 'bg-blue-500', label: 'In Call', pulse: true },
  completed: { color: 'bg-emerald-500', label: 'Completed', pulse: false },
  failed: { color: 'bg-red-500', label: 'Failed', pulse: false },
}

export function CallStatusBadge({ status }: CallStatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending

  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        {config.pulse && (
          <span
            className={`absolute inline-flex h-full w-full animate-ping rounded-full ${config.color} opacity-75`}
          />
        )}
        <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${config.color}`} />
      </span>
      <span className="text-sm text-zinc-300">{config.label}</span>
    </div>
  )
}
