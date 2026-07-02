<template>
  <div class="login-page">
    <div class="login-card">
      <h2 class="title">校园智能问答助手</h2>
      <div class="role-tabs">
        <div
          v-for="r in roleOptions"
          :key="r.value"
          class="role-tab"
          :class="{ active: form.role === r.value }"
          @click="form.role = r.value"
        >
          {{ r.label }}
        </div>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" :placeholder="form.role === 'student' ? '学号' : '用户名'" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin" size="large" style="width: 100%">登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const formRef = ref()

const form = reactive({
  username: '',
  password: '',
  role: 'student' as 'student' | 'admin',
})

const roleOptions = [
  { label: '学生', value: 'student' as const },
  { label: '管理员', value: 'admin' as const },
]

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.login(form.username, form.password, form.role)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}
.login-card {
  width: 360px;
  padding: 40px 32px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.title {
  text-align: center;
  margin-bottom: 28px;
  font-size: 20px;
  font-weight: 500;
  color: #303133;
}
.role-tabs {
  display: flex;
  margin-bottom: 28px;
  border-bottom: 1px solid #e4e7ed;
}
.role-tab {
  flex: 1;
  text-align: center;
  padding-bottom: 12px;
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  position: relative;
  transition: color 0.2s;
}
.role-tab:hover {
  color: #606266;
}
.role-tab.active {
  color: #303133;
  font-weight: 500;
}
.role-tab.active::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -1px;
  transform: translateX(-50%);
  width: 32px;
  height: 2px;
  background: #409eff;
  border-radius: 1px;
}

/* 为错误提示预留固定高度，避免提示出现/消失时布局跳动 */
.login-card :deep(.el-form-item) {
  margin-bottom: 20px;
}
.login-card :deep(.el-form-item__content) {
  min-height: 52px;
}
</style>
