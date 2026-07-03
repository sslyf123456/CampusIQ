export interface Student {
  id: number
  student_id: string
  name: string
  gender?: string
  department?: string
  major?: string
  phone?: string
  email?: string
  birth_date?: string
  enrollment_year?: number
  dorm_building?: string
  dorm_room?: string
}

export interface StudentListResponse {
  data: Student[]
  total: number
  page: number
  page_size: number
}

export interface StudentCreate {
  student_id: string
  name: string
  password: string
  gender?: string
  department?: string
  major?: string
  phone?: string
  email?: string
  birth_date?: string
  enrollment_year?: number
  dorm_building?: string
  dorm_room?: string
}

export interface StudentUpdate {
  name?: string
  gender?: string
  department?: string
  major?: string
  phone?: string
  email?: string
  birth_date?: string
  enrollment_year?: number
  dorm_building?: string
  dorm_room?: string
}

export const GENDER_MAP: Record<string, string> = { male: '男', female: '女' }
