<template>
  <div class="notice-page">
    <el-card shadow="never">
      <div class="page-header">
        <h2>校园通知</h2>
        <div style="display:flex;gap:12px;align-items:center;">
          <el-input v-model="keyword" placeholder="搜索通知..." clearable @keyup.enter="loadData" style="width:220px" size="small" />
          <el-button @click="loadData" size="small">搜索</el-button>
          <el-button type="primary" @click="showDlg(null)" v-if="isAdmin">+ 发布通知</el-button>
        </div>
      </div>

      <el-table :data="list" stripe empty-text="暂无通知">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">{{ CATEGORY_MAP[row.category] || row.category }}</template>
        </el-table-column>
        <el-table-column prop="publisher" label="发布人" width="100" />
        <el-table-column label="发布时间" width="170">
          <template #default="{ row }">{{ formatTime(row.published_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">查看</el-button>
            <template v-if="isAdmin">
              <el-button size="small" @click="showDlg(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 查看详情弹窗 -->
    <el-dialog :title="detail?.title" v-model="detailVisible" width="600px">
      <div class="notice-detail" v-if="detail">
        <div class="meta">
          <span>{{ CATEGORY_MAP[detail.category] || detail.category }}</span>
          <span>{{ detail.publisher || '-' }}</span>
          <span>{{ formatTime(detail.published_at) }}</span>
        </div>
        <div class="content">{{ detail.content }}</div>
      </div>
    </el-dialog>

    <!-- 发布/编辑弹窗 -->
    <el-dialog :title="dlgTitle" v-model="dlgVisible" width="600px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category">
            <el-option label="通知" value="general" />
            <el-option label="学术" value="academic" />
            <el-option label="宿舍" value="dormitory" />
            <el-option label="奖助" value="scholarship" />
          </el-select>
        </el-form-item>
        <el-form-item label="正文" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlgVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getNoticesApi, createNoticeApi, updateNoticeApi, deleteNoticeApi } from '@/api/notice'
import type { Notice } from '@/types/notice'

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const list = ref<Notice[]>([])
const keyword = ref('')

// 详情
const detailVisible = ref(false)
const detail = ref<Notice | null>(null)
function showDetail(row: Notice) {
  detail.value = row
  detailVisible.value = true
}

// 发布/编辑
const dlgVisible = ref(false)
const dlgTitle = ref('发布通知')
const saving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref()
const form = ref<Partial<Notice>>({})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入正文', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

const CATEGORY_MAP: Record<string, string> = {
  general: '通知',
  academic: '学术',
  dormitory: '宿舍',
  scholarship: '奖助',
}

async function loadData() {
  try {
    const res = await getNoticesApi({ keyword: keyword.value || undefined })
    list.value = res
  } catch {
    ElMessage.error('加载失败')
  }
}

function showDlg(row: Notice | null) {
  if (row) {
    dlgTitle.value = '编辑通知'
    editingId.value = row.id
    form.value = { ...row }
  } else {
    dlgTitle.value = '发布通知'
    editingId.value = null
    form.value = { category: 'general', title: '', content: '' }
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
      await updateNoticeApi(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createNoticeApi(form.value)
      ElMessage.success('发布成功')
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
  await ElMessageBox.confirm('确定删除该通知？', '提示', { type: 'warning' })
  try {
    await deleteNoticeApi(id)
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
.notice-page { max-width: 1200px; margin: 0 auto; height: 100%; }
.notice-page :deep(.el-card) { height: 100%; display: flex; flex-direction: column; }
.notice-page :deep(.el-card__body) { flex: 1; display: flex; flex-direction: column; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 8px; flex-shrink: 0; }
.page-header h2 { font-size: 18px; font-weight: 500; color: #303133; }
.notice-page :deep(.el-table) { border: 1px solid #ebeef5; border-radius: 4px; box-sizing: border-box; }
.notice-page :deep(.el-table__inner-wrapper) { border: none; }
.notice-detail .meta { display: flex; gap: 16px; color: #909399; font-size: 13px; margin-bottom: 16px; }
.notice-detail .content { white-space: pre-wrap; line-height: 1.8; color: #303133; }
</style>
