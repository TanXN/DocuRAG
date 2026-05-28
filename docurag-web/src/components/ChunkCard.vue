<script setup lang="ts">
import type { RagChunk } from '../api/chat'
import SourceTag from './SourceTag.vue'

defineProps<{
  chunk: RagChunk
}>()

function formatScore(value?: number) {
  return value === undefined || value === null ? '-' : Number(value).toFixed(4)
}
</script>

<template>
  <div class="chunk-card">
    <div class="chunk-head">
      <SourceTag :source-id="chunk.source_id" :metadata="chunk.metadata" />
      <el-tag v-if="chunk.retrieval_type" type="success" effect="plain">
        {{ chunk.retrieval_type }}
      </el-tag>
    </div>

    <el-descriptions :column="4" size="small" border class="score-grid">
      <el-descriptions-item label="BM25">{{ formatScore(chunk.bm25_score) }}</el-descriptions-item>
      <el-descriptions-item label="Distance">{{ formatScore(chunk.distance) }}</el-descriptions-item>
      <el-descriptions-item label="Rerank">{{ formatScore(chunk.rerank_score) }}</el-descriptions-item>
      <el-descriptions-item label="Chunk">{{ chunk.metadata?.chunk_index ?? '-' }}</el-descriptions-item>
    </el-descriptions>

    <div class="chunk-document">{{ chunk.document || '暂无片段内容' }}</div>
  </div>
</template>

<style scoped>
.chunk-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chunk-head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.score-grid {
  width: 100%;
}

.chunk-document {
  padding: 12px 14px;
  color: #374151;
  line-height: 1.75;
  white-space: pre-wrap;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}
</style>
