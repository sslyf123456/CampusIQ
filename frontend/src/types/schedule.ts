export interface Schedule {
  id: number
  course_name: string
  teacher: string
  weekday: number
  start_period: number
  end_period: number
  location: string
  start_week: number
  end_week: number
  semester: string
}

export interface ScheduleListResponse {
  data: Schedule[]
  total: number
  page: number
  page_size: number
}

export const WEEKDAY_MAP: Record<number, string> = {
  1: '周一',
  2: '周二',
  3: '周三',
  4: '周四',
  5: '周五',
  6: '周六',
  7: '周日',
}
