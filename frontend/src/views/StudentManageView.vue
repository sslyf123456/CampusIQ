<template>
  <div class="student-page">
    <el-card shadow="never">
      <div class="page-header">
        <h2>学生管理</h2>
        <el-button type="primary" @click="showDlg(null)">+ 添加学生</el-button>
      </div>

      <!-- 搜索栏 -->
      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="学号 / 姓名 / 院系" clearable style="width: 240px" @keyup.enter="handleSearch" />
        <el-button @click="handleSearch">查询</el-button>
      </div>

      <el-table :data="list" stripe empty-text="暂无学生数据" v-loading="loading">
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="性别" width="70">
          <template #default="{ row }">{{ GENDER_MAP[row.gender] || '-' }}</template>
        </el-table-column>
        <el-table-column prop="department" label="院系" min-width="140" />
        <el-table-column prop="major" label="专业" min-width="140" />
        <el-table-column prop="enrollment_year" label="入学年份" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column label="宿舍" width="120">
          <template #default="{ row }">
            {{ [row.dorm_building, row.dorm_room].filter(Boolean).join(' ') || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDlg(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="dlgTitle" v-model="dlgVisible" width="560px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="学号" prop="student_id">
          <el-input v-model="form.student_id" :disabled="!!editingId" placeholder="如 20230001" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingId">
          <el-input v-model="form.password" type="password" show-password placeholder="6-64位" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="form.gender" placeholder="请选择" clearable>
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
          </el-select>
        </el-form-item>
        <el-form-item label="院系" prop="department">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="专业" prop="major">
          <el-input v-model="form.major" />
        </el-form-item>
        <el-form-item label="入学年份" prop="enrollment_year">
          <el-input v-model="form.enrollment_year" placeholder="如 2023" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="出生日期" prop="birth_date">
          <el-date-picker v-model="form.birth_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="宿舍楼" prop="dorm_building">
          <el-input v-model="form.dorm_building" />
        </el-form-item>
        <el-form-item label="宿舍号" prop="dorm_room">
          <el-input v-model="form.dorm_room" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlgVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStudentsApi, createStudentApi, updateStudentApi, deleteStudentApi } from '@/api/student'
import { GENDER_MAP } from '@/types/student'
import type { Student, StudentCreate, StudentUpdate } from '@/types/student'

const list = ref<Student[]>([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const dlgVisible = ref(false)
const dlgTitle = ref('添加学生')
const saving = ref(false)
const editingId = ref<string | null>(null)
const formRef = ref()
const form = ref<Partial<StudentCreate & StudentUpdate>>({})

const rules = {
  student_id: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { max: 32, message: '最多32个字符', trigger: 'blur' },
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { max: 64, message: '最多64个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度 6-64 位', trigger: 'blur' },
  ],
  gender: [
    { pattern: /^(male|female)$/, message: '请选择性别', trigger: 'change' },
  ],
  department: [
    { max: 128, message: '最多128个字符', trigger: 'blur' },
  ],
  major: [
    { max: 128, message: '最多128个字符', trigger: 'blur' },
  ],
  enrollment_year: [
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (!value) { callback(); return }
        if (!/^\d{4}$/.test(String(value))) { callback(new Error('请输入4位年份，如 2023')); return }
        const y = Number(value)
        if (y < 2000 || y > 2099) { callback(new Error('年份范围 2000-2099')); return }
        callback()
      },
      trigger: 'blur',
    },
  ],
  phone: [
    { max: 20, message: '最多20个字符', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  email: [
    { max: 128, message: '最多128个字符', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱', trigger: 'blur' },
  ],
  dorm_building: [
    { max: 32, message: '最多32个字符', trigger: 'blur' },
  ],
  dorm_room: [
    { max: 16, message: '最多16个字符', trigger: 'blur' },
  ],
}

async function loadData() {
  loading.value = true
  try {
    const res = await getStudentsApi({
      keyword: keyword.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    list.value = res.data
    total.value = res.total
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadData()
}

function showDlg(row: Student | null) {
  if (row) {
    dlgTitle.value = '编辑学生'
    editingId.value = row.student_id
    form.value = { ...row }
  } else {
    dlgTitle.value = '添加学生'
    editingId.value = null
    form.value = { gender: 'male', enrollment_year: 2023 }
  }
  dlgVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
  editingId.value = null
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = { ...form.value }
    if (payload.enrollment_year) {
      payload.enrollment_year = Number(payload.enrollment_year)
    } else {
      delete payload.enrollment_year
    }
    if (editingId.value) {
      const data: StudentUpdate = payload
      delete (data as any).student_id
      delete (data as any).password
      delete (data as any).id
      await updateStudentApi(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createStudentApi(payload as StudentCreate)
      ElMessage.success('添加成功')
    }
    dlgVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Student) {
  await ElMessageBox.confirm(`确定删除学生 ${row.name}（${row.student_id}）？`, '提示', { type: 'warning' })
  try {
    await deleteStudentApi(row.student_id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.student-page {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
}

.student-page :deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.student-page :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.student-page :deep(.el-table) {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  box-sizing: border-box;
}

.student-page :deep(.el-table__inner-wrapper) {
  border: none;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.page-header h2 {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  flex-shrink: 0;
}
</style>
