# AGENTS.md — Frontend (Next.js)

Read root `AGENTS.md` first. This file governs the `frontend/` directory only.

## Setup Commands
```bash
npm install
npm run dev        # development
npm run build      # production build — must pass with 0 errors
npm run lint       # must pass before task is done
```

Fix all TypeScript errors and lint warnings before marking a task done.

---

## Key Constraints

- App Router only. No Pages Router patterns.
- All data fetching in Server Components unless Realtime or interactivity is needed.
- Supabase Realtime subscriptions go in Client Components marked `'use client'`.
- Never use `any` type. Define all types in `types/index.ts`.
- shadcn/ui components only — do not install other UI libraries.
- Never use HTML `<form>` tags. Use `onClick` + `useState` for form interactions.

---

## Types (types/index.ts)

```typescript
export type CustomerStatus = 'pending' | 'scheduled' | 'in_call' | 'completed' | 'failed'
export type RiskLabel = 'Healthy' | 'Monitor' | 'At-Risk'
export type Sentiment = 'positive' | 'neutral' | 'frustrated'
export type Recommendation = 'escalate' | 'monitor' | 'healthy'

export interface Customer {
  id: string
  name: string
  email: string
  phone: string  // E.164 format: +919876543210
  company: string | null
  product_name: string | null
  days_since_signup: number | null
  csm_name: string | null
  status: CustomerStatus
  bolna_execution_id: string | null  // Bolna uses execution_id, not call_id
  created_at: string
}

export interface CallResult {
  id: string
  customer_id: string
  bolna_execution_id: string
  transcript: string | null
  duration_seconds: number | null
  health_score: number | null
  risk_label: RiskLabel | null
  key_blocker: string | null
  sentiment: Sentiment | null
  recommendation: Recommendation | null
  recording_url: string | null
  answered_by_voicemail: boolean
  created_at: string
}

export interface CustomerWithResult extends Customer {
  call_result: CallResult | null
}
```

---

## Supabase Client (lib/supabase.ts)

```typescript
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

This is a singleton. Import from here everywhere — never call `createClient` again.

---

## Backend API Calls (lib/api.ts)

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL
const headers = {
  'Content-Type': 'application/json',
  'x-api-key': process.env.NEXT_PUBLIC_ADMIN_API_KEY!
}

export async function getCustomers(): Promise<CustomerWithResult[]> { ... }
export async function uploadCSV(file: File): Promise<{ created: number; skipped: number }> { ... }
export async function triggerCampaign(customerIds: string[]): Promise<void> { ... }
export async function assignCSM(customerId: string): Promise<void> { ... }
```

All functions throw on non-2xx. Wrap call sites in try/catch and show toast on error.

---

## Component Conventions

### CustomerTable.tsx
- `'use client'` — subscribes to Supabase Realtime
- Receives initial data as prop from Server Component
- On Supabase INSERT to `call_results` → update the matching row in local state
- Columns: Name, Company, Days Since Signup, Status, Health Score, Risk, Blocker, Actions
- Clicking "View Transcript" opens TranscriptModal

### UploadCSV.tsx
- Drag-and-drop area + file input fallback
- Validate file is `.csv` before sending
- Show upload progress and result (`3 customers created, 1 skipped`)
- After successful upload, refresh customer list

### HealthScoreBadge.tsx
```typescript
// Color coding:
// score >= 70 → green background
// score 40-69 → yellow background  
// score < 40  → red background
// null → grey "Pending"
```

### CallStatusBadge.tsx
```typescript
// pending   → grey dot
// scheduled → blue dot + "Calling..."
// in_call   → blue dot + pulse animation
// completed → green dot
// failed    → red dot
```

### TranscriptModal.tsx
- shadcn/ui Dialog component
- Full transcript in scrollable `<pre>` block with monospace font
- Show: duration, health score, sentiment, key blocker at top
- Close on Escape or backdrop click

---

## Realtime Subscription Pattern

```typescript
'use client'
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

// In CustomerTable component:
useEffect(() => {
  const channel = supabase
    .channel('call_results_changes')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'call_results' },
      (payload) => {
        // Update the matching customer row with new call result
        setCustomers(prev => prev.map(c => 
          c.id === payload.new.customer_id 
            ? { ...c, status: 'completed', call_result: payload.new as CallResult }
            : c
        ))
      }
    )
    .subscribe()

  return () => { supabase.removeChannel(channel) }
}, [])
```

---

## Environment Variables (frontend)

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_ADMIN_API_KEY=
```

---

## Page Layout (app/page.tsx)

```
Header: "ChurnGuard" logo + "Start Campaign" button (disabled if no customers)

Section 1: Upload CSV
  UploadCSV component

Section 2: Customer Dashboard  
  CustomerTable component (real-time)
  Summary stats: Total | Healthy | Monitor | At-Risk | Pending

No sidebar. Single-column layout. Max-width 1200px centered.
```

---

## What Not to Build

- No login page or auth UI
- No settings page
- No charts or graphs (out of scope for demo)
- No multi-page routing (single page app)
- No dark mode toggle (pick one and stick with it)