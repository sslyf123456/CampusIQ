import axios from 'axios'
import { getToken, removeToken } from '@/utils/token'
import type { Router } from 'vue-router'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 列表接口后端返回 { data: [...], total, page, page_size }
// 详情/操作接口后端直接返回对象，无 data 包装
// 此处不解包，由各 API 调用处自行处理 res.data
request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeToken()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default request
