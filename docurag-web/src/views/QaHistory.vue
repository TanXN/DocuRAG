<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AnswerCard from '../components/AnswerCard.vue'
import ChunkCard from '../components/ChunkCard.vue'
import { getHistory, type HistoryItem } from '../api/history'
import type { RagChunk } from '../api/chat'

type NormalizedHistoryItem = Omit<HistoryItem, 'chunks'> & {
  chunks: RagChunk[]
}

const loading = ref(false)
const tableData = ref<NormalizedHistoryItem[]>([])
const detailVisible = ref(false)
const currentDetail = ref<NormalizedHistoryItem | null>(null)
const activeChunks = ref<string[]>([])

const detailChunks = computed(() => currentDetail.value?.chunks ?? [])

function summary(text: string, length = 80) {
  if (!text) return '-'
  return text.length > length ? `${text.slice(0, length)}...` : text
}

function normalizeChunks(chunks: HistoryItem['chunks']): RagChunk[] {
  if (Array.isArray(chunks)) {
    return chunks
  }
  if (typeof chunks === 'string' && chunks.trim()) {
    try {
      const parsed = JSON.parse(chunks)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
}

function normalizeHistoryItem(item: HistoryItem): NormalizedHistoryItem {
  return {
    ...item,
    chunks: normalizeChunks(item.chunks),
  }
}

async function loadHistory() {
  loading.value = true
  try {
    const res = await getHistory(50)
    tableData.value = (res.data.data ?? []).map(normalizeHistoryItem)
  } catch {
    ElMessage.error('获取问答历史失败')
  } finally {
    loading.value = false
  }
}

function showDetail(row: NormalizedHistoryItem) {
  detailVisible.value = true
  currentDetail.value = row
  activeChunks.value = row.chunks.map((_, index) => String(index))
}

function removeHistory() {
  ElMessage.warning('当前后端暂未提供删除单条历史接口')
}

function handleClearHistory() {
  ElMessage.warning('当前后端暂未提供清空历史接口')
}

onMounted(loadHistory)
</script>

<template>
  <el-card shadow="never" class="page-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <div>
          <div class="title">问答日志</div>
          <div class="subtitle">展示最近 50 条问答历史，数据来自 /api/reg/rag-history。</div>
        </div>
        <div class="actions">
          <el-button @click="loadHistory">刷新</el-button>
          <el-button type="danger" plain disabled @click="handleClearHistory">清空历史</el-button>
        </div>
      </div>
    </template>

    <el-table :data="tableData" stripe empty-text="暂无历史记录">
      <el-table-column prop="id" label="ID" width="90" />
      <el-table-column prop="question" label="问题" min-width="220" show-overflow-tooltip />
      <el-table-column label="答案摘要" min-width="300">
        <template #default="{ row }">
          {{ summary(row.answer) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="300" fixed="right" align="center">
        <template #default="{ row }">
          <div class="table-actions">
            <el-button size="small" type="primary" @click="showDetail(row)">查看详情</el-button>
            <el-button size="small" text @click="ElMessage.success('已点赞')">点赞</el-button>
            <el-button size="small" text @click="ElMessage.success('已点踩')">点踩</el-button>
            <el-button size="small" type="danger" text disabled @click="removeHistory">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="detailVisible" title="问答详情" width="860px">
    <div class="detail-content">
      <el-card shadow="never" class="detail-card">
        <template #header>
          <div class="title">问题</div>
        </template>
        <div class="question-text">{{ currentDetail?.question }}</div>
      </el-card>

      <AnswerCard :answer="currentDetail?.answer" />

      <el-card shadow="never" class="detail-card">
        <template #header>
          <div class="card-header">
            <span class="title">命中片段</span>
            <el-tag>{{ detailChunks.length }} 条</el-tag>
          </div>
        </template>
        <el-collapse v-if="detailChunks.length" v-model="activeChunks">
          <el-collapse-item
            v-for="(chunk, index) in detailChunks"
            :key="`${chunk.source_id || index}-${index}`"
            :name="String(index)"
            :title="`[${chunk.source_id || `S${index}`}] ${chunk.metadata?.file_name || '未知文件'}`"
          >
            <ChunkCard :chunk="chunk" />
          </el-collapse-item>
        </el-collapse>
        <el-empty v-else description="暂无命中片段" />
      </el-card>
    </div>
  </el-dialog>
</template>

<style scoped>
.page-card,
.detail-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title {
  font-weight: 700;
  color: #111827;
}

.subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #6b7280;
}

.actions {
  display: flex;
  gap: 10px;
}

.table-actions {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  white-space: nowrap;
}

.table-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-text {
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
