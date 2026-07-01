export interface ScholarshipRecord {
  id: number
  student_id: number
  type: string
  name: string
  amount?: string
  status: 'pending' | 'approved' | 'rejected'
  semester: string
  note?: string
  created_at: string
  updated_at: string
}

export interface ScholarshipListResponse {
  data: ScholarshipRecord[]
  total: number
  page: number
  page_size: number
}

export const STATUS_MAP: Record<string, string> = {
  pending: '审核中',
  approved: '已发放',
  rejected: '已拒绝',
}

export const STATUS_TAG: Record<string, 'warning' | 'success' | 'danger'> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
}
