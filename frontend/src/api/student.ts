import request from './request'
import type { Student, StudentListResponse, StudentCreate, StudentUpdate } from '@/types/student'
import type { Schedule } from '@/types/schedule'

// 列表：后端返回 { data: [...], total, page, page_size }
export async function getStudentsApi(params?: { keyword?: string; page?: number; page_size?: number }) {
  const res = await request.get<StudentListResponse>('/campus/students', { params })
  return res.data
}

// 详情/增改：后端直接返回对象，无外层 data 包装
export async function getStudentApi(studentId: string) {
  const res = await request.get<Student>(`/campus/students/${studentId}`)
  return res.data
}

export async function createStudentApi(data: StudentCreate) {
  const res = await request.post<Student>('/campus/students', data)
  return res.data
}

export async function updateStudentApi(studentId: string, data: StudentUpdate) {
  const res = await request.put<Student>(`/campus/students/${studentId}`, data)
  return res.data
}

export async function deleteStudentApi(studentId: string) {
  await request.delete(`/campus/students/${studentId}`)
}

// 管理员：查看学生选课列表
export async function getStudentSchedulesApi(studentId: string) {
  const res = await request.get<Schedule[]>(`/campus/students/${studentId}/schedules`)
  return res.data
}
