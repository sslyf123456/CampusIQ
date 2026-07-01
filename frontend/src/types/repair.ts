export interface RepairOrder {
  id: number
  student_id: number
  description: string
  location?: string
  contact_phone?: string
  status: 'pending' | 'processing' | 'completed'
  handler?: string
  handle_note?: string
  submitted_at: string
  processed_at?: string
  completed_at?: string
}

export interface RepairListResponse {
  data: RepairOrder[]
  total: number
  page: number
  page_size: number
}

export const STATUS_MAP: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
}

export const STATUS_TAG: Record<string, 'warning' | 'primary' | 'success'> = {
  pending: 'warning',
  processing: 'primary',
  completed: 'success',
}
