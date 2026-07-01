<template>
  <div class="profile-page">
    <el-card shadow="never">
      <h2 class="page-title">个人信息</h2>
      <el-descriptions :column="2" border v-if="user">
        <el-descriptions-item label="学号">{{ user.student_id || user.username }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ user.name }}</el-descriptions-item>
        <el-descriptions-item label="院系">{{ user.department || '-' }}</el-descriptions-item>
        <el-descriptions-item label="专业">{{ user.major || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="user.role === 'admin' ? 'danger' : 'primary'" style="transition: none;">
            {{ user.role === 'admin' ? '管理员' : '学生' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ user.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ user.phone || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-skeleton :rows="5" animated v-else />

      <h3 class="section-title">修改密码</h3>
      <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="100px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleChangePwd">确认修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { getProfileApi, changePasswordApi } from '@/api/auth'

const auth = useAuthStore()
const user = ref(auth.user)

const pwdFormRef = ref()
const loading = ref(false)
const pwdForm = ref({
  old_password: '',
  new_password: '',
})

const pwdRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

onMounted(async () => {
  if (!auth.user) {
    try {
      const res = await getProfileApi()
      // getProfileApi 返回 AxiosResponse<User>，实际数据在 res.data
      auth.user = res.data
      user.value = res.data
      auth.role = res.data.role
    } catch {
      ElMessage.error('获取个人信息失败')
    }
  }
})

async function handleChangePwd() {
  const valid = await pwdFormRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await changePasswordApi(pwdForm.value)
    ElMessage.success('密码修改成功')
    pwdForm.value = { old_password: '', new_password: '' }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-page { max-width: 700px; margin: 0 auto; height: 100%; }
.profile-page :deep(.el-card) { height: 100%; }
.page-title { font-size: 18px; font-weight: 500; margin-bottom: 20px; color: #303133; }
.section-title { font-size: 16px; font-weight: 500; margin: 32px 0 16px; color: #303133; }
</style>
