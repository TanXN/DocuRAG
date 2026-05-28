<script setup lang="ts">
defineProps<{
  answer?: string
}>()
</script>

<template>
  <el-card class="answer-card" shadow="never">
    <template #header>
      <div class="card-title">回答</div>
    </template>
    <div class="answer-text">{{ answer || '等待提问后展示回答。' }}</div>
  </el-card>
</template>

<style scoped>
.answer-card {
  border-radius: 8px;
}

.card-title {
  font-weight: 600;
  color: #111827;
}

.answer-text {
  min-height: 96px;
  color: #374151;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
