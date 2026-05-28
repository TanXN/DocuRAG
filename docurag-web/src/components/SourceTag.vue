<script setup lang="ts">
import type { ChunkMetadata } from '../api/chat'

defineProps<{
  sourceId?: string
  metadata?: ChunkMetadata
}>()
</script>

<template>
  <el-tag class="source-tag" type="info" effect="light">
    [{{ sourceId || 'S?' }}]
    {{ metadata?.file_name || '未知文件' }}
    <span v-if="metadata?.page">/ 第 {{ metadata.page }} 页</span>
    <span v-if="metadata?.chunk_index !== undefined">/ chunk {{ metadata.chunk_index }}</span>
  </el-tag>
</template>

<style scoped>
.source-tag {
  max-width: 100%;
  height: auto;
  min-height: 28px;
  padding: 4px 8px;
  white-space: normal;
  line-height: 1.5;
}
</style>
