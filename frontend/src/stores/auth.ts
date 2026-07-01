import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types/user'
import { getToken, setToken, removeToken } from '@/utils/token'
import { loginApi, getProfileApi, logoutApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getToken())
  const user = ref<User | null>(null)
  const role = ref<'student' | 'admin' | null>(null)
  const isLoggedIn = ref(!!token.value)

  async function login(username: string, password: string, loginRole: 'student' | 'admin') {
    const res = await loginApi({ username, password, role: loginRole })
    // loginApi 返回 AxiosResponse<{token, user}>，实际数据在 res.data
    token.value = res.data.token
    user.value = res.data.user
    role.value = res.data.user.role
    isLoggedIn.value = true
    setToken(res.data.token)
  }

  async function fetchProfile() {
    const res = await getProfileApi()
    user.value = res.data
    role.value = res.data.role
  }

  async function logout() {
    try {
      await logoutApi()
    } catch {
      // 即使后端调用失败也清理本地状态
    }
    token.value = null
    user.value = null
    role.value = null
    isLoggedIn.value = false
    removeToken()
  }

  return { token, user, role, isLoggedIn, login, fetchProfile, logout }
})
