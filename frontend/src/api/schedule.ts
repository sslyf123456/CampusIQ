import request from './request'
import type { Schedule, ScheduleListResponse } from '@/types/schedule'

// 学生和管理员共用：后端根据 JWT role 区分返回数据
// 后端返回格式：{ data: [...], total, page, page_size }
export async function getSchedulesApi(params?: { semester?: string; page?: number; page_size?: number }) {
  const res = await request.get<ScheduleListResponse>('/campus/schedules', { params })
  return res.data
}

// 管理员：创建课程，后端返回 { data: {...} }
export async function createScheduleApi(data: Partial<Schedule>) {
  const res = await request.post<{ data: Schedule }>('/campus/schedules', data)
  return res.data.data
}

// 管理员：更新课程
export async function updateScheduleApi(id: number, data: Partial<Schedule>) {
  const res = await request.put<{ data: Schedule }>(`/campus/schedules/${id}`, data)
  return res.data.data
}

// 管理员：删除课程
export async function deleteScheduleApi(id: number) {
  await request.delete(`/campus/schedules/${id}`)
}

// 管理员：添加选课学生
export async function addScheduleStudentsApi(id: number, studentIds: string[]) {
  await request.post(`/campus/schedules/${id}/students`, { student_ids: studentIds })
}

// 管理员：移除选课学生
export async function removeScheduleStudentApi(scheduleId: number, studentId: string) {
  await request.delete(`/campus/schedules/${scheduleId}/students/${studentId}`)
}
