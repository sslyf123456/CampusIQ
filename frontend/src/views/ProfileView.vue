<template>
  <div class="profile-page">
    <el-card shadow="never">
      <h2 class="page-title">个人信息</h2>
      <div v-if="loading" class="profile-loading">
        <el-skeleton :rows="5" animated />
      </div>
      <template v-else-if="user">
        <InfoTable :rows="infoRows">
          <template #role>
            <el-tag :type="user.role === 'admin' ? 'success' : 'primary'" style="transition: none;">
              {{ user.role === 'admin' ? '管理员' : '学生' }}
            </el-tag>
          </template>
        </InfoTable>
      </template>
      <div v-else class="profile-error">
        <div class="error-title">加载失败</div>
        <div class="error-desc">无法获取个人信息，请稍后重试</div>
        <el-button type="primary" @click="loadProfile">重新加载</el-button>
      </div>

      <template v-if="user">
        <h3 class="section-title">修改密码</h3>
        <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="70px" class="pwd-form">
          <el-form-item label="旧密码" prop="old_password">
            <el-input v-model="pwdForm.old_password" type="password" show-password style="width: 200px;" />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="pwdForm.new_password" type="password" show-password style="width: 200px;" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="pwdLoading" @click="handleChangePwd">确认修改</el-button>
          </el-form-item>
        </el-form>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { getProfileApi, changePasswordApi } from '@/api/auth'
import InfoTable from '@/components/InfoTable.vue'

const auth = useAuthStore()
const router = useRouter()
const user = ref(auth.user)
const loading = ref(true)

const infoRows = computed(() => {
  if (!user.value) return []
  const rows: { key: string; label: string; value: string }[] = []
  if (user.value.role !== 'admin') {
    rows.push({ key: 'student_id', label: '学号', value: user.value.student_id || '-' })
  }
  if (user.value.role === 'admin') {
    rows.push({ key: 'username', label: '用户名', value: user.value.username || '-' })
  } else {
    rows.push({ key: 'name', label: '姓名', value: user.value.name || '-' })
  }
  rows.push({ key: 'role', label: '角色', value: '' })
  if (user.value.role !== 'admin') {
    rows.push({ key: 'gender', label: '性别', value: user.value.gender === 'male' ? '男' : user.value.gender === 'female' ? '女' : user.value.gender || '-' })
    rows.push({ key: 'department', label: '院系', value: user.value.department || '-' })
    rows.push({ key: 'major', label: '专业', value: user.value.major || '-' })
    rows.push({ key: 'enrollment_year', label: '入学年份', value: user.value.enrollment_year ? String(user.value.enrollment_year) : '-' })
    rows.push({ key: 'birth_date', label: '出生日期', value: user.value.birth_date || '-' })
  }
  rows.push({ key: 'email', label: '邮箱', value: user.value.email || '-' })
  rows.push({ key: 'phone', label: '电话', value: user.value.phone || '-' })
  if (user.value.role !== 'admin') {
    rows.push({ key: 'dorm', label: '宿舍', value: user.value.dorm_building ? `${user.value.dorm_building} ${user.value.dorm_room}` : '-' })
  }
  return rows
})

const pwdFormRef = ref()
const pwdLoading = ref(false)
const pwdForm = ref({
  old_password: '',
  new_password: '',
})

const pwdRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度 6-64 位', trigger: 'blur' },
  ],
}

async function loadProfile() {
  loading.value = true
  try {
    const res = await getProfileApi()
    auth.user = res.data
    user.value = res.data
    auth.role = res.data.role
  } catch {
    ElMessage.error('获取个人信息失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadProfile)

async function handleChangePwd() {
  const valid = await pwdFormRef.value?.validate().catch(() => false)
  if (!valid) return
  pwdLoading.value = true
  try {
    await changePasswordApi(pwdForm.value)
    ElMessage.success('密码修改成功，请重新登录')
    pwdForm.value = { old_password: '', new_password: '' }
    await auth.logout()
    router.push('/login')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}
</script>

<style scoped>
.profile-page {
  max-width: 700px;
  margin: 0 auto;
  height: 100%;
}

.profile-page :deep(.el-card) {
  height: 100%;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 20px;
  color: #303133;
}

.profile-loading {
  padding: 16px 0;
}

.profile-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 0;
  color: #606266;
}

.error-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.error-desc {
  font-size: 14px;
  color: #909399;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin: 32px 0 16px;
  color: #303133;
}

/* 为错误提示预留固定高度，避免提示出现/消失时布局跳动 */
.profile-page :deep(.el-form-item) {
  margin-bottom: 25px;
}

.profile-page :deep(.el-form-item__content) {
  min-height: 18px;
}

.pwd-form {
  margin: 0;
}

.pwd-form :deep(.el-form-item) {
  margin-bottom: 25px;
}

.pwd-form :deep(.el-form-item__label) {
  justify-content: flex-start;
}
</style>
