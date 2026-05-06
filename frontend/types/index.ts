export type CustomerStatus = 'pending' | 'scheduled' | 'in_call' | 'completed' | 'failed'
export type RiskLabel = 'Healthy' | 'Monitor' | 'At-Risk'
export type Sentiment = 'positive' | 'neutral' | 'frustrated'
export type Recommendation = 'escalate' | 'monitor' | 'healthy'

export interface Customer {
  id: string
  name: string
  email: string
  phone: string
  company: string | null
  product_name: string | null
  days_since_signup: number | null
  csm_name: string | null
  status: CustomerStatus
  bolna_execution_id: string | null
  created_at: string
  call_result: CallResult | null
}

export interface CallResult {
  id: string
  customer_id: string
  bolna_execution_id: string
  transcript: string | null
  duration_seconds: number | null
  completed: boolean
  health_score: number | null
  risk_label: RiskLabel | null
  key_blocker: string | null
  sentiment: Sentiment | null
  recommendation: Recommendation | null
  recording_url: string | null
  answered_by_voicemail: boolean
  created_at: string
}

export interface APIResponse<T = unknown> {
  success: boolean
  data: T
  error: string | null
}

export interface UploadResult {
  created: number
  skipped: number
  errors: string[]
}

export interface CampaignResult {
  triggered: number
  failed: number
  errors: string[]
}
