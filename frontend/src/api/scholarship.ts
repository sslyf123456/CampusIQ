import request from './request'
import type { ScholarshipRecord, ScholarshipListResponse } from '@/types/scholarship'

// 获取奖助记录：后端根据 JWT role 区分，返回 { data: [...], total, ... }
export async function getScholarshipsApi(params?: { status?: string; page?: number; page_size?: number }) {
  const res = await request.get<ScholarshipListResponse>('/campus/scholarships', { params })
  return res.data.data
}

// 管理员：创建记录，返回 { data: {...} }
export async function createScholarshipApi(data: Partial<ScholarshipRecord>) {
  const res = await request.post<{ data: ScholarshipRecord }>('/campus/scholarships', data)
  return res.data.data
}

// 管理员：更新记录
export async function updateScholarshipApi(id: number, data: Partial<ScholarshipRecord>) {
  const res = await request.put<{ data: ScholarshipRecord }>(`/campus/scholarships/${id}`, data)
  return res.data.data
}

// 管理员：删除记录
export async function deleteScholarshipApi(id: number) {
  await request.delete(`/campus/scholarships/${id}`)
}
