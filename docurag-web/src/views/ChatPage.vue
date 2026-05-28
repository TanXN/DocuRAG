<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AnswerCard from '../components/AnswerCard.vue'
import ChunkCard from '../components/ChunkCard.vue'
import SourceTag from '../components/SourceTag.vue'
import { askQuestion, type ChatResult, type RagChunk } from '../api/chat'

const question = ref('')
const loading = ref(false)
const result = ref<ChatResult | null>(null)
const activeChunks = ref<string[]>([])

const examples = [
  '后端服务端口是多少？',
  'greenhouse-api.service 怎么重启？',
  'Nginx 配置文件路径是什么？',
  '设备超过多久不上报会被判断为离线？',
  'MySQL 备份目录在哪里？',
  '温度达到多少会触发二级报警？',
]

const chunks = computed<RagChunk[]>(() => result.value?.chunks ?? [])

function selectExample(text: string) {
  question.value = text
}

function sourceLabel(chunk: RagChunk, index: number) {
  return chunk.source_id || `S${index}`
}

function fileName(chunk: RagChunk) {
  return chunk.metadata?.file_name || '未知文件'
}

function pageLabel(chunk: RagChunk) {
  return chunk.metadata?.page ? `第 ${chunk.metadata.page} 页` : '页码未知'
}

function scoreLabel(value?: number) {
  return value === undefined || value === null ? '-' : Number(value).toFixed(4)
}

async function submitQuestion() {
  const text = question.value.trim()
  if (!text) {
    ElMessage.error('请输入问题')
    return
  }

  loading.value = true
  try {
    const res = await askQuestion(text)
    result.value = res.data.data
    activeChunks.value = chunks.value.map((_, index) => String(index))
    ElMessage.success('提问成功')
  } catch {
    ElMessage.error('提问失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="chat-page">
    <el-card shadow="never" class="question-card">
      <template #header>
        <div class="panel-heading">
          <div>
            <div class="title">智能问答</div>
            <div class="subtitle">输入问题后将执行 Hybrid 检索与 Rerank。</div>
          </div>
          <el-tag type="primary" effect="light">RAG v2</el-tag>
        </div>
      </template>

      <div class="question-editor">
        <el-input
          v-model="question"
          type="textarea"
          :rows="9"
          resize="none"
          placeholder="请输入你想查询的企业知识库问题"
        />
      </div>

      <el-button
        class="ask-button"
        type="primary"
        size="large"
        :loading="loading"
        @click="submitQuestion"
      >
        提问
      </el-button>

      <div class="example-block">
        <div class="example-title">示例问题</div>
        <div class="example-list">
          <button
            v-for="item in examples"
            :key="item"
            class="example-button"
            type="button"
            @click="selectExample(item)"
          >
            {{ item }}
          </button>
        </div>
      </div>
    </el-card>

    <div class="answer-column" v-loading="loading">
      <AnswerCard :answer="result?.answer" />

      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-header">
            <span class="title">引用来源</span>
            <el-tag>{{ chunks.length }} 条</el-tag>
          </div>
        </template>

        <div v-if="chunks.length" class="source-list">
          <div
            v-for="(chunk, index) in chunks"
            :key="`${chunk.source_id || index}-${index}`"
            class="source-item"
          >
            <SourceTag
              :source-id="sourceLabel(chunk, index)"
              :metadata="chunk.metadata"
            />
          </div>
        </div>
        <el-empty v-else description="暂无引用来源" />
      </el-card>

      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-header">
            <span class="title">命中片段</span>
            <el-tag type="success">Rerank</el-tag>
          </div>
        </template>

        <el-collapse v-if="chunks.length" v-model="activeChunks">
          <el-collapse-item
            v-for="(chunk, index) in chunks"
            :key="`${chunk.source_id || index}-${index}`"
            :name="String(index)"
          >
            <template #title>
              <div class="chunk-title">
                <el-tag size="small" type="info" effect="dark">
                  {{ sourceLabel(chunk, index) }}
                </el-tag>
                <span class="chunk-file">{{ fileName(chunk) }}</span>
                <span class="chunk-meta">{{ pageLabel(chunk) }}</span>
                <span class="chunk-meta">chunk {{ chunk.metadata?.chunk_index ?? '-' }}</span>
                <el-tag size="small" type="success" effect="light">
                  rerank {{ scoreLabel(chunk.rerank_score) }}
                </el-tag>
              </div>
            </template>
            <ChunkCard :chunk="chunk" />
          </el-collapse-item>
        </el-collapse>
        <el-empty v-else description="提问后展示命中片段" />
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: grid;
  grid-template-columns: minmax(340px, 400px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
  max-width: 1480px;
  margin: 0 auto;
}

.question-card,
.section-card {
  border-radius: 8px;
  border-color: #e6ebf2;
}

.question-card {
  overflow: hidden;
}

.question-card :deep(.el-card__header),
.section-card :deep(.el-card__header) {
  padding: 16px 18px;
}

.question-card :deep(.el-card__body) {
  padding: 18px;
}

.title {
  font-weight: 700;
  color: #111827;
}

.subtitle {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: #6b7280;
}

.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.question-editor {
  padding: 2px;
  background: #f8fafc;
  border: 1px solid #eef2f7;
  border-radius: 8px;
}

.question-editor :deep(.el-textarea__inner) {
  padding: 14px;
  line-height: 1.7;
  border: 0;
  box-shadow: none;
}

.ask-button {
  width: 100%;
  height: 42px;
  margin-top: 18px;
  font-weight: 700;
}

.example-block {
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid #eef2f7;
}

.example-title {
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #6b7280;
}

.example-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.example-button {
  width: 100%;
  min-height: 40px;
  padding: 9px 12px;
  color: #374151;
  text-align: left;
  cursor: pointer;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease;
}

.example-button:hover {
  color: #2563eb;
  background: #eff6ff;
  border-color: #93c5fd;
}

.answer-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.answer-column :deep(.answer-card),
.section-card {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.source-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 10px;
}

.source-item {
  min-width: 0;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid #eef2f7;
  border-radius: 8px;
}

.chunk-title {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  gap: 10px;
  padding-right: 10px;
}

.chunk-file {
  min-width: 120px;
  overflow: hidden;
  font-weight: 600;
  color: #111827;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chunk-meta {
  flex: 0 0 auto;
  font-size: 13px;
  color: #6b7280;
}

.section-card :deep(.el-collapse) {
  border-top: 0;
  border-bottom: 0;
}

.section-card :deep(.el-collapse-item__header) {
  min-height: 54px;
  padding: 0 12px;
  background: #f8fafc;
  border: 1px solid #eef2f7;
  border-radius: 8px;
}

.section-card :deep(.el-collapse-item + .el-collapse-item) {
  margin-top: 10px;
}

.section-card :deep(.el-collapse-item__wrap) {
  border-bottom: 0;
}

.section-card :deep(.el-collapse-item__content) {
  padding: 14px 2px 4px;
}

@media (max-width: 1100px) {
  .chat-page {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .chat-page {
    gap: 16px;
  }

  .chunk-title {
    flex-wrap: wrap;
    padding: 8px 8px 8px 0;
  }

  .chunk-file {
    min-width: 0;
    max-width: 100%;
  }
}
</style>
