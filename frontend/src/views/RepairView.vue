<template>
  <div class="repair-page">
    <el-card shadow="never">
      <div class="page-header">
        <h2>宿舍报修</h2>
        <el-button type="primary" @click="showCreateDlg" v-if="!isAdmin">+ 发起报修</el-button>
      </div>

      <el-table :data="list" stripe empty-text="暂无报修记录">
        <el-table-column prop="description" label="问题描述" min-width="200" />
        <el-table-column prop="location" label="地点" width="120" />
        <el-table-column prop="contact_phone" label="联系电话" width="130" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="STATUS_TAG[row.status]" style="transition: none;">{{ STATUS_MAP[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handler" label="处理人" width="100" />
        <el-table-column prop="handle_note" label="处理备注" min-width="120" />
        <el-table-column label="提交时间" width="170">
          <template #default="{ row }">{{ formatTime(row.submitted_at) }}</template>
        </el-table-column>
        <el-table-column label="处理时间" width="170">
          <template #default="{ row }">{{ formatTime(row.processed_at) || formatTime(row.completed_at) || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" v-if="isAdmin">
          <template #default="{ row }">
            <el-button size="small" @click="showHandleDlg(row)">处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 发起报修弹窗 -->
    <el-dialog title="发起报修" v-model="createVisible" width="500px">
      <el-form :model="createForm" :rules="createRules" ref="createRef" label-width="100px">
        <el-form-item label="问题描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="报修地点" prop="location">
          <el-input v-model="createForm.location" placeholder="如：1号楼302" />
        </el-form-item>
        <el-form-item label="联系方式" prop="contact_phone">
          <el-input v-model="createForm.contact_phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>

    <!-- 管理员处理弹窗 -->
    <el-dialog title="处理工单" v-model="handleVisible" width="500px">
      <el-form :model="handleForm" label-width="100px">
        <el-form-item label="状态">
          <el-select v-model="handleForm.status">
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理人">
          <el-input v-model="handleForm.handler" />
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input v-model="handleForm.handle_note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { createRepairOrderApi, getRepairOrdersApi, updateRepairOrderApi } from '@/api/repair'
import { STATUS_MAP, STATUS_TAG } from '@/types/repair'
import type { RepairOrder } from '@/types/repair'

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const list = ref<RepairOrder[]>([])

// 发起报修
const createVisible = ref(false)
const saving = ref(false)
const createRef = ref()
const createForm = ref({ description: '', location: '', contact_phone: '' })
const createRules = {
  description: [{ required: true, message: '请输入问题描述', trigger: 'blur' }],
}

function showCreateDlg() {
  createForm.value = { description: '', location: '', contact_phone: '' }
  createVisible.value = true
}

async function handleCreate() {
  const valid = await createRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await createRepairOrderApi(createForm.value)
    ElMessage.success('报修已提交')
    createVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    saving.value = false
  }
}

// 管理员处理
const handleVisible = ref(false)
const handleForm = ref<{ id: number; status: string; handler: string; handle_note: string }>({
  id: 0, status: 'processing', handler: '', handle_note: ''
})
function showHandleDlg(row: RepairOrder) {
  handleForm.value = {
    id: row.id,
    status: row.status === 'pending' ? 'processing' : 'completed',
    handler: row.handler || '',
    handle_note: row.handle_note || '',
  }
  handleVisible.value = true
}
async function handleSave() {
  saving.value = true
  try {
    await updateRepairOrderApi(handleForm.value.id, {
      status: handleForm.value.status,
      handler: handleForm.value.handler,
      handle_note: handleForm.value.handle_note,
    })
    ElMessage.success('处理成功')
    handleVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function loadData() {
  try {
    const res = await getRepairOrdersApi()
    list.value = res
  } catch {
    ElMessage.error('加载失败')
  }
}

function formatTime(t: string): string {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

onMounted(loadData)
</script>

<style scoped>
.repair-page { max-width: 1200px; margin: 0 auto; height: 100%; }
.repair-page :deep(.el-card) { height: 100%; display: flex; flex-direction: column; }
.repair-page :deep(.el-card__body) { flex: 1; display: flex; flex-direction: column; }
.page-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-shrink: 0;
}
.page-header h2 { font-size: 18px; font-weight: 500; color: #303133; }
.repair-page :deep(.el-table) { border: 1px solid #ebeef5; border-radius: 4px; box-sizing: border-box; }
.repair-page :deep(.el-table__inner-wrapper) { border: none; }
</style>
