<template>
  <div class="scholarship-page">
    <el-card shadow="never">
      <div class="page-header">
        <h2>奖助记录</h2>
        <el-button type="primary" @click="showDlg(null)" v-if="isAdmin">+ 添加记录</el-button>
      </div>

      <el-table :data="list" stripe empty-text="暂无奖助记录">
        <el-table-column v-if="isAdmin" prop="student_no" label="学号" width="120" />
        <el-table-column v-if="isAdmin" prop="student_name" label="姓名" width="100" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="name" label="奖项名称" />
        <el-table-column prop="amount" label="金额（元）" width="120" align="right">
          <template #default="{ row }">{{ row.amount != null ? Number(row.amount).toFixed(2) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="STATUS_TAG[row.status]" style="transition: none;">{{ STATUS_MAP[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="semester" label="学期" width="140" />
        <el-table-column prop="note" label="备注" min-width="120" />
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" v-if="isAdmin">
          <template #default="{ row }">
            <el-button size="small" @click="showDlg(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <!-- 增删改弹窗 -->
    <el-dialog :title="dlgTitle" v-model="dlgVisible" width="500px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择">
            <el-option label="奖学金" value="奖学金" />
            <el-option label="助学金" value="助学金" />
          </el-select>
        </el-form-item>
        <el-form-item label="奖项名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input
            v-model="form.amount"
            placeholder="请输入金额"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status">
            <el-option label="审核中" value="pending" />
            <el-option label="已发放" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="学期" prop="semester">
          <el-input v-model="form.semester" placeholder="如 2025-2026-1" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="2" />
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
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getScholarshipsApi, createScholarshipApi, updateScholarshipApi, deleteScholarshipApi
} from '@/api/scholarship'
import { STATUS_MAP, STATUS_TAG } from '@/types/scholarship'
import type { ScholarshipRecord } from '@/types/scholarship'

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const list = ref<ScholarshipRecord[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const dlgVisible = ref(false)
const dlgTitle = ref('添加记录')
const saving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref()
const form = ref<Partial<ScholarshipRecord>>({})

const rules = {
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  name: [
    { required: true, message: '请输入奖项名称', trigger: 'blur' },
    { max: 128, message: '最多128个字符', trigger: 'blur' },
  ],
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (!/^\d+(\.\d{1,2})?$/.test(value)) {
          callback(new Error('金额须为数字，最多两位小数'))
        } else if (parseFloat(value) < 0) {
          callback(new Error('金额不能为负数'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
  semester: [
    { required: true, message: '请输入学期', trigger: 'blur' },
    { pattern: /^\d{4}-\d{4}-[12]$/, message: '格式如 2025-2026-1', trigger: 'blur' },
  ],
}

async function loadData() {
  try {
    const res = await getScholarshipsApi({ page: page.value, page_size: pageSize.value })
    list.value = res.data
    total.value = res.total
  } catch {
    ElMessage.error('加载失败')
  }
}

function showDlg(row: ScholarshipRecord | null) {
  if (row) {
    dlgTitle.value = '编辑记录'
    editingId.value = row.id
    form.value = { ...row }
  } else {
    dlgTitle.value = '添加记录'
    editingId.value = null
    form.value = { type: '奖学金', status: 'pending', semester: '2025-2026-1' }
  }
  dlgVisible.value = true
}

function resetForm() { formRef.value?.resetFields() }

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingId.value) {
      await updateScholarshipApi(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createScholarshipApi(form.value)
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
  await ElMessageBox.confirm('确定删除该记录？', '提示', { type: 'warning' })
  try {
    await deleteScholarshipApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function formatTime(t: string): string {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

onMounted(loadData)
</script>

<style scoped>
.scholarship-page {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
}

.scholarship-page :deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.scholarship-page :deep(.el-card__body) {
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

.scholarship-page :deep(.el-table) {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  box-sizing: border-box;
}

.scholarship-page :deep(.el-table__inner-wrapper) {
  border: none;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  flex-shrink: 0;
}
</style>
