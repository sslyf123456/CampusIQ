<template>
  <div class="schedule-page">
    <el-card shadow="never">
      <div class="page-header">
        <h2>{{ isAdmin ? '课程管理' : '课表查询' }}</h2>
        <div v-if="isAdmin">
          <el-button type="primary" @click="showDlg(null)">+ 添加课程</el-button>
        </div>
      </div>

      <!-- 学期筛选 -->
      <div class="filter-bar">
        <span class="filter-label">学期筛选</span>
        <el-select v-model="filterSemester" placeholder="全部学期" clearable style="width: 200px" @change="handleFilterChange">
          <el-option v-for="s in semesterOptions" :key="s" :label="s" :value="s" />
        </el-select>
      </div>

      <!-- 学生视图：本周课表 -->
      <template v-if="!isAdmin">
        <el-table :data="scheduleList" stripe empty-text="暂无课程数据">
          <el-table-column prop="weekday" label="星期" width="80" :formatter="(r: any) => WEEKDAY_MAP[r.weekday]" />
          <el-table-column prop="course_name" label="课程名称" />
          <el-table-column prop="teacher" label="任课老师" width="120" />
          <el-table-column label="上课时间" width="180">
            <template #default="{ row }">
              第{{ row.start_period }}–{{ row.end_period }}节
            </template>
          </el-table-column>
          <el-table-column prop="location" label="教室" width="120" />
          <el-table-column label="起止周" width="120">
            <template #default="{ row }">
              第{{ row.start_week }}–{{ row.end_week }}周
            </template>
          </el-table-column>
          <el-table-column prop="semester" label="学期" width="130" />
        </el-table>
      </template>

      <!-- 管理员视图：课程管理 -->
      <template v-else>
        <el-table :data="scheduleList" stripe empty-text="暂无课程数据">
          <el-table-column prop="course_name" label="课程名称" />
          <el-table-column prop="teacher" label="任课老师" width="120" />
          <el-table-column prop="weekday" label="星期" width="80" :formatter="(r: any) => WEEKDAY_MAP[r.weekday]" />
          <el-table-column label="时间" width="160">
            <template #default="{ row }">
              第{{ row.start_period }}–{{ row.end_period }}节
            </template>
          </el-table-column>
          <el-table-column prop="location" label="教室" width="120" />
          <el-table-column label="起止周" width="120">
            <template #default="{ row }">
              第{{ row.start_week }}–{{ row.end_week }}周
            </template>
          </el-table-column>
          <el-table-column prop="semester" label="学期" width="120" />
          <el-table-column label="操作" width="230" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showStudentsDlg(row)">选课学生</el-button>
              <el-button size="small" @click="showDlg(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>

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
    <el-dialog :title="dlgTitle" v-model="dlgVisible" width="500px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="课程名称" prop="course_name">
          <el-input v-model="form.course_name" />
        </el-form-item>
        <el-form-item label="任课老师" prop="teacher">
          <el-input v-model="form.teacher" />
        </el-form-item>
        <el-form-item label="星期" prop="weekday">
          <el-select v-model="form.weekday" placeholder="请选择">
            <el-option v-for="(v,k) in WEEKDAY_MAP" :key="k" :label="v" :value="Number(k)" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始节次" prop="start_period">
          <el-select v-model="form.start_period" placeholder="请选择">
            <el-option v-for="p in 12" :key="p" :label="`第${p}节`" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="结束节次" prop="end_period">
          <el-select v-model="form.end_period" placeholder="请选择">
            <el-option v-for="p in 12" :key="p" :label="`第${p}节`" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="教室" prop="location">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="学期" prop="semester">
          <el-input v-model="form.semester" placeholder="如 2025-2026-1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlgVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 选课学生查看弹窗 -->
    <el-dialog :title="`${studentsCourseName} 的选课学生`" v-model="studentsVisible" width="640px">
      <el-table :data="studentsList" stripe empty-text="暂无学生选此课程" v-loading="studentsLoading" max-height="400">
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="性别" width="70">
          <template #default="{ row }">{{ GENDER_MAP[row.gender] || '-' }}</template>
        </el-table-column>
        <el-table-column prop="department" label="院系" min-width="120" />
        <el-table-column prop="major" label="专业" min-width="120" />
        <el-table-column label="宿舍" width="120">
          <template #default="{ row }">
            {{ [row.dorm_building, row.dorm_room].filter(Boolean).join(' ') || '-' }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="studentsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getSchedulesApi, createScheduleApi, updateScheduleApi, deleteScheduleApi,
  addScheduleStudentsApi, removeScheduleStudentApi, getScheduleStudentsApi, getSemestersApi
} from '@/api/schedule'
import { WEEKDAY_MAP } from '@/types/schedule'
import { GENDER_MAP } from '@/types/student'
import type { Schedule } from '@/types/schedule'
import type { Student } from '@/types/student'

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')

const scheduleList = ref<Schedule[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 学期筛选
const filterSemester = ref<string>('')
const semesterOptions = ref<string[]>([])

// 弹窗
const dlgVisible = ref(false)
const dlgTitle = ref('添加课程')
const saving = ref(false)
const formRef = ref()
const editingId = ref<number | null>(null)
const form = ref<Partial<Schedule>>({})

const rules = {
  course_name: [
    { required: true, message: '请输入课程名称', trigger: 'blur' },
    { max: 128, message: '最多128个字符', trigger: 'blur' },
  ],
  weekday: [{ required: true, message: '请选择星期', trigger: 'change' }],
  start_period: [
    { required: true, message: '请输入开始节次', trigger: 'blur' },
    { type: 'number', min: 1, max: 12, message: '节次范围 1-12', trigger: 'blur' },
  ],
  end_period: [
    { required: true, message: '请输入结束节次', trigger: 'blur' },
    { type: 'number', min: 1, max: 12, message: '节次范围 1-12', trigger: 'blur' },
    {
      validator: (_rule: any, value: number, callback: any) => {
        if (form.value.start_period != null && value < form.value.start_period) callback(new Error('结束节次不能小于开始节次'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  start_week: [
    { type: 'number', min: 1, max: 20, message: '周次范围 1-20', trigger: 'blur' },
  ],
  end_week: [
    { type: 'number', min: 1, max: 20, message: '周次范围 1-20', trigger: 'blur' },
    {
      validator: (_rule: any, value: number, callback: any) => {
        if (form.value.start_week != null && value < form.value.start_week) callback(new Error('结束周次不能小于开始周次'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  semester: [
    { required: true, message: '请输入学期', trigger: 'blur' },
    { pattern: /^\d{4}-\d{4}-[12]$/, message: '格式如 2025-2026-1', trigger: 'blur' },
  ],
}

async function loadData() {
  loading.value = true
  try {
    const params: { semester?: string; page?: number; page_size?: number } = {}
    if (filterSemester.value) params.semester = filterSemester.value
    params.page = page.value
    params.page_size = pageSize.value
    const res = await getSchedulesApi(params)
    scheduleList.value = res.data
    total.value = res.total
  } catch {
    ElMessage.error('加载课表失败')
  } finally {
    loading.value = false
  }
}

async function loadSemesters() {
  try {
    semesterOptions.value = await getSemestersApi()
  } catch {
    // 忽略，学期列表加载失败不影响主流程
  }
}

function handleFilterChange() {
  page.value = 1
  loadData()
}

function showDlg(row: Schedule | null) {
  if (row) {
    dlgTitle.value = '编辑课程'
    editingId.value = row.id
    form.value = { ...row }
  } else {
    dlgTitle.value = '添加课程'
    editingId.value = null
    form.value = { weekday: 1, start_period: 1, end_period: 2, semester: '2025-2026-1' }
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
    if (editingId.value) {
      await updateScheduleApi(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createScheduleApi(form.value)
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

async function handleDelete(id: number) {
  await ElMessageBox.confirm('确定删除该课程？', '提示', { type: 'warning' })
  try {
    await deleteScheduleApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  loadData()
  loadSemesters()
})

// 选课学生查看
const studentsVisible = ref(false)
const studentsLoading = ref(false)
const studentsList = ref<Student[]>([])
const studentsCourseName = ref('')

async function showStudentsDlg(row: Schedule) {
  studentsCourseName.value = `${row.course_name}（${WEEKDAY_MAP[row.weekday]} 第${row.start_period}-${row.end_period}节）`
  studentsVisible.value = true
  studentsLoading.value = true
  studentsList.value = []
  try {
    studentsList.value = await getScheduleStudentsApi(row.id)
  } catch {
    ElMessage.error('加载选课学生失败')
  } finally {
    studentsLoading.value = false
  }
}
</script>

<style scoped>
.schedule-page {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
}

.schedule-page :deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.schedule-page :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
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

.filter-label {
  font-size: 14px;
  color: #606266;
}

.schedule-page :deep(.el-table) {
  border-radius: 4px;
}

.schedule-page :deep(.el-table__inner-wrapper) {
  border: none;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  flex-shrink: 0;
}
</style>
