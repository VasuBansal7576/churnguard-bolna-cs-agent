'use client'

import { Badge } from '@/components/ui/badge'

interface HealthScoreBadgeProps {
  score: number | null
}

export function HealthScoreBadge({ score }: HealthScoreBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <Badge variant="outline" className="bg-zinc-800/50 text-zinc-400 border-zinc-700">
        Pending
      </Badge>
    )
  }

  if (score >= 70) {
    return (
      <Badge className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25">
        {score}
      </Badge>
    )
  }

  if (score >= 40) {
    return (
      <Badge className="bg-amber-500/15 text-amber-400 border border-amber-500/30 hover:bg-amber-500/25">
        {score}
      </Badge>
    )
  }

  return (
    <Badge className="bg-red-500/15 text-red-400 border border-red-500/30 hover:bg-red-500/25">
      {score}
    </Badge>
  )
}
