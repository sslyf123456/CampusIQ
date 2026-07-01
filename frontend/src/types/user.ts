export interface User {
  student_id?: string
  username?: string
  name: string
  role: 'student' | 'admin'
  department?: string
  major?: string
  gender?: string
  phone?: string
  email?: string
  birth_date?: string
  enrollment_year?: number
  dorm_building?: string
  dorm_room?: string
}

export interface LoginRequest {
  username: string
  password: string
  role: 'student' | 'admin'
}

export interface LoginResponse {
  token: string
  user: User
}
