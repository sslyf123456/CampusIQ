<template>
  <div class="sidenav">
    <div class="logo">校园助手</div>
    <el-menu
      :default-active="activeMenu"
      class="nav-menu"
      @select="handleSelect"
    >
      <el-menu-item index="/profile">
        <el-icon><User /></el-icon>
        <span>个人信息</span>
      </el-menu-item>
      <el-menu-item index="/students" v-if="isAdmin">
        <el-icon><UserFilled /></el-icon>
        <span>学生管理</span>
      </el-menu-item>
      <el-menu-item index="/schedule">
        <el-icon><Calendar /></el-icon>
        <span>课表</span>
      </el-menu-item>
      <el-menu-item index="/repair">
        <el-icon><Tools /></el-icon>
        <span>宿舍报修</span>
      </el-menu-item>
      <el-menu-item index="/scholarship">
        <el-icon><Money /></el-icon>
        <span>奖助记录</span>
      </el-menu-item>
      <el-menu-item index="/notice">
        <el-icon><Bell /></el-icon>
        <span>校园通知</span>
      </el-menu-item>
      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <span>AI 问答</span>
      </el-menu-item>
    </el-menu>
    <div class="logout" @click="handleLogout">
      <el-icon><SwitchButton /></el-icon>
      <span>退出登录</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import {
  User, UserFilled, Calendar, Tools, Money, Bell, ChatDotRound, SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isAdmin = computed(() => auth.user?.role === 'admin')
const activeMenu = computed(() => '/' + (route.path.split('/')[1] || 'profile'))

function handleSelect(path: string) {
  router.push(path)
}

async function handleLogout() {
  await auth.logout()
  ElMessage.info('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.sidenav {
  width: 200px;
  height: 100vh;
  background: #fff;
  border-right: 1.5px solid #dcdfe6;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  border-bottom: 1.5px solid #dcdfe6;
}
.nav-menu {
  flex: 1;
  border-right: none;
}
.logout {
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #909399;
  font-size: 14px;
  border-top: 1.5px solid #dcdfe6;
}
.logout:hover {
  color: #409eff;
}
</style>
