import request from './request'
import type { Notice, NoticeListResponse } from '@/types/notice'

// 查看通知列表：返回 { data: [...], total, ... }
export async function getNoticesApi(params?: { keyword?: string; category?: string; page?: number; page_size?: number }) {
  const res = await request.get<NoticeListResponse>('/campus/notices', { params })
  return res.data.data
}

// 管理员：发布通知，返回 { data: {...} }
export async function createNoticeApi(data: Partial<Notice>) {
  const res = await request.post<{ data: Notice }>('/campus/notices', data)
  return res.data.data
}

// 管理员：编辑通知
export async function updateNoticeApi(id: number, data: Partial<Notice>) {
  const res = await request.put<{ data: Notice }>(`/campus/notices/${id}`, data)
  return res.data.data
}

// 管理员：删除通知
export async function deleteNoticeApi(id: number) {
  await request.delete(`/campus/notices/${id}`)
}
