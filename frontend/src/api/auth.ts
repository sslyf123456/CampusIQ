import request from './request'
import type { User, LoginRequest } from '@/types/user'

// 登录：后端返回 { token, user }
export function loginApi(data: LoginRequest) {
  return request.post<{ token: string; user: User }>('/campus/auth/login', data)
}

// 获取当前用户信息：后端返回 { role, student_id, name, ... }
export function getProfileApi() {
  return request.get<User>('/campus/auth/me')
}

// 修改密码：后端返回 { detail: "密码修改成功" }
export function changePasswordApi(data: { old_password: string; new_password: string }) {
  return request.put('/campus/auth/password', data)
}

// 退出登录：后端返回 { detail: "已退出登录" }
export function logoutApi() {
  return request.post('/campus/auth/logout')
}
