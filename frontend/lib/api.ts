import type { APIResponse, Customer, UploadResult, CampaignResult } from '@/types'

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_ADMIN_API_KEY || ''

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': API_KEY,
      ...options.headers,
    },
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }

  return res.json()
}

export async function getCustomers(): Promise<Customer[]> {
  const res = await apiFetch<APIResponse<Customer[]>>('/api/customers/')
  return res.data
}

export async function getCustomer(id: string): Promise<Customer> {
  const res = await apiFetch<APIResponse<Customer>>(`/api/customers/${id}`)
  return res.data
}

export async function uploadCSV(file: File): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${BASE_URL}/api/customers/upload`, {
    method: 'POST',
    headers: { 'x-api-key': API_KEY },
    body: formData,
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Upload error ${res.status}: ${text}`)
  }

  const json: APIResponse<UploadResult> = await res.json()
  return json.data
}

export async function triggerCampaign(customerIds: string[]): Promise<CampaignResult> {
  const res = await apiFetch<APIResponse<CampaignResult>>('/api/campaigns/trigger', {
    method: 'POST',
    body: JSON.stringify({ customer_ids: customerIds }),
  })
  return res.data
}

export async function updateCustomer(
  id: string,
  update: { csm_name?: string; status?: string }
): Promise<Customer> {
  const res = await apiFetch<APIResponse<Customer>>(`/api/customers/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
  return res.data
}
