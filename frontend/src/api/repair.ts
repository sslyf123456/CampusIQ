import request from './request'
import type { RepairOrder, RepairListResponse } from '@/types/repair'

// 学生发起报修：后端返回 { data: {...} }
export async function createRepairOrderApi(data: { description: string; location?: string; contact_phone?: string }) {
  const res = await request.post<{ data: RepairOrder }>('/campus/repair-orders', data)
  return res.data.data
}

// 获取工单列表：后端根据 JWT role 区分，返回 { data: [...], total, page, page_size }
export async function getRepairOrdersApi(params?: { status?: string; page?: number; page_size?: number }) {
  const res = await request.get<RepairListResponse>('/campus/repair-orders', { params })
  return res.data
}

// 管理员：更新工单状态，返回 { data: {...} }
export async function updateRepairOrderApi(
  id: number,
  data: {
    status: string
    handler?: string
    handle_note?: string
    processed_at?: string
    completed_at?: string
  }
) {
  const res = await request.put<{ data: RepairOrder }>(`/campus/repair-orders/${id}`, data)
  return res.data.data
}
