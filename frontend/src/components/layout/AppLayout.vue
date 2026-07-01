<template>
  <div class="layout">
    <SideNav />
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import SideNav from '@/components/layout/SideNav.vue'
</script>

<style scoped>
.layout {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
.main-content {
  flex: 1;
  overflow: auto;
  padding: 32px 40px;
  background: #f5f7fa;
}
</style>
