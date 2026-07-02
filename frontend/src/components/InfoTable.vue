<template>
  <div class="info-table-wrapper">
    <table class="info-table">
      <tr v-for="row in rows" :key="row.label">
        <td class="info-label">{{ row.label }}</td>
        <td class="info-value"><slot :name="row.key" :row="row">{{ row.value }}</slot></td>
      </tr>
    </table>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  rows: { key: string; label: string; value: string }[]
}>()
</script>

<style scoped>
.info-table-wrapper {
  border: 1.5px solid #d4c5a8;
  border-radius: 4px;
  overflow: hidden;
}

.info-table {
  width: 100%;
  border-collapse: collapse;
  border-style: hidden;
}

.info-table td {
  border: 1.5px solid #d4c5a8;
  padding: 6px 16px;
  font-size: 14px;
  color: #303133;
}

.info-label {
  width: 90px;
  background: #f5f0e6;
  color: #8c7a62;
  white-space: nowrap;
}

.info-value {
  background: #fdfcf9;
}
</style>
