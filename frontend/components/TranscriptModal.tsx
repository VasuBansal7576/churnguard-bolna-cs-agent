'use client'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { HealthScoreBadge } from './HealthScoreBadge'
import type { CallResult } from '@/types'

interface TranscriptModalProps {
  callResult: CallResult | null
  customerName: string
  open: boolean
  onClose: () => void
}

export function TranscriptModal({ callResult, customerName, open, onClose }: TranscriptModalProps) {
  if (!callResult) return null

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '—'
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}m ${s}s`
  }

  const sentimentColors: Record<string, string> = {
    positive: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    neutral: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
    frustrated: 'bg-red-500/15 text-red-400 border-red-500/30',
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto bg-zinc-900 border-zinc-800 text-zinc-100">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold text-zinc-100">
            Call Transcript — {customerName}
          </DialogTitle>
        </DialogHeader>

        {/* Metrics bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3">
          <div className="rounded-lg bg-zinc-800/50 border border-zinc-700/50 p-3">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Health Score</p>
            <div className="mt-1">
              <HealthScoreBadge score={callResult.health_score} />
            </div>
          </div>
          <div className="rounded-lg bg-zinc-800/50 border border-zinc-700/50 p-3">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Duration</p>
            <p className="mt-1 text-sm font-medium text-zinc-200">
              {formatDuration(callResult.duration_seconds)}
            </p>
          </div>
          <div className="rounded-lg bg-zinc-800/50 border border-zinc-700/50 p-3">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Sentiment</p>
            <div className="mt-1">
              {callResult.sentiment ? (
                <Badge className={sentimentColors[callResult.sentiment] || sentimentColors.neutral}>
                  {callResult.sentiment}
                </Badge>
              ) : (
                <span className="text-sm text-zinc-500">—</span>
              )}
            </div>
          </div>
          <div className="rounded-lg bg-zinc-800/50 border border-zinc-700/50 p-3">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Risk</p>
            <p className="mt-1 text-sm font-medium text-zinc-200">
              {callResult.risk_label || '—'}
            </p>
          </div>
        </div>

        {/* Key blocker */}
        {callResult.key_blocker && (
          <div className="rounded-lg bg-red-500/5 border border-red-500/20 p-3">
            <p className="text-xs text-red-400 uppercase tracking-wider font-medium">Key Blocker</p>
            <p className="mt-1 text-sm text-zinc-300">{callResult.key_blocker}</p>
          </div>
        )}

        {/* Transcript */}
        <div className="mt-2">
          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Transcript</p>
          <div className="rounded-lg bg-zinc-950 border border-zinc-800 p-4 max-h-[40vh] overflow-y-auto">
            <pre className="text-sm text-zinc-300 whitespace-pre-wrap font-mono leading-relaxed">
              {callResult.transcript || 'No transcript available.'}
            </pre>
          </div>
        </div>

        {/* Recording link */}
        {callResult.recording_url && (
          <div className="mt-2">
            <a
              href={callResult.recording_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-400 hover:text-blue-300 underline underline-offset-2"
            >
              🎧 Listen to recording
            </a>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
