export interface Notice {
  id: number
  title: string
  content: string
  category: string
  publisher: string
  published_at: string
  updated_at: string
}

export interface NoticeListResponse {
  data: Notice[]
  total: number
  page: number
  page_size: number
}

export const CATEGORY_MAP: Record<string, string> = {
  academic: '教学通知',
  dormitory: '宿舍通知',
  scholarship: '奖助通知',
  general: '综合通知',
}
