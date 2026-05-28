<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getHistory } from '../api/history'

const qaCount = ref(0)
const loading = ref(false)

const stats = computed(() => [
  { label: '知识库数量', value: '1', desc: '默认知识库' },
  { label: '文档数量', value: '1', desc: '暂无列表接口，静态展示' },
  { label: '问答次数', value: qaCount.value, desc: '来自历史记录接口' },
  { label: '当前检索模式', value: 'Hybrid + Rerank', desc: '向量 + BM25 + 重排' },
])

const capabilities = [
  'PDF / TXT / Markdown 解析',
  'ChromaDB 向量检索',
  'Elasticsearch BM25 关键词检索',
  'CrossEncoder Rerank',
  '来源引用',
  '问答历史',
]

onMounted(async () => {
  loading.value = true
  try {
    const res = await getHistory(50)
    qaCount.value = res.data.data?.length ?? 0
  } catch {
    ElMessage.error('获取问答次数失败')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <div class="stats-grid">
      <el-card v-for="item in stats" :key="item.label" shadow="never" class="stat-card">
        <div class="stat-label">{{ item.label }}</div>
        <div class="stat-value">{{ item.value }}</div>
        <div class="stat-desc">{{ item.desc }}</div>
      </el-card>
    </div>

    <el-card shadow="never" class="capability-card">
      <template #header>
        <div class="section-title">系统能力</div>
      </template>
      <el-row :gutter="16">
        <el-col v-for="item in capabilities" :key="item" :xs="24" :sm="12" :md="8">
          <div class="capability-item">
            <span class="dot"></span>
            {{ item }}
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card,
.capability-card {
  border-radius: 8px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.stat-value {
  margin-top: 12px;
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.stat-desc {
  margin-top: 8px;
  font-size: 13px;
  color: #9ca3af;
}

.section-title {
  font-weight: 700;
  color: #111827;
}

.capability-item {
  display: flex;
  align-items: center;
  min-height: 48px;
  padding: 12px 14px;
  margin-bottom: 14px;
  color: #374151;
  background: #f8fafc;
  border: 1px solid #eef2f7;
  border-radius: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  margin-right: 10px;
  background: #2563eb;
  border-radius: 50%;
}

@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
