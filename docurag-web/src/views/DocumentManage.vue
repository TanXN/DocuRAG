<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, type UploadRequestOptions } from 'element-plus'
import { uploadDocument } from '../api/document'

interface UploadRecord {
  filename: string
  type: string
  chunkCount: number | string
  status: 'success' | 'failed'
  uploadedAt: string
}

const loading = ref(false)
const records = ref<UploadRecord[]>([])
const lastResult = ref<{ filename: string; chunkCount: number } | null>(null)

function getFileType(filename: string) {
  const index = filename.lastIndexOf('.')
  return index >= 0 ? filename.slice(index).toLowerCase() : '-'
}

function nowText() {
  return new Date().toLocaleString()
}

async function handleUpload(options: UploadRequestOptions) {
  const file = options.file as File
  loading.value = true
  try {
    const res = await uploadDocument(file)
    const data = res.data.data
    lastResult.value = {
      filename: data.filename,
      chunkCount: data.chunk_count,
    }
    records.value.unshift({
      filename: data.filename,
      type: getFileType(data.filename),
      chunkCount: data.chunk_count,
      status: 'success',
      uploadedAt: nowText(),
    })
    ElMessage.success(res.data.msg || '上传成功')
    options.onSuccess?.(res.data)
  } catch (error) {
    records.value.unshift({
      filename: file.name,
      type: getFileType(file.name),
      chunkCount: '-',
      status: 'failed',
      uploadedAt: nowText(),
    })
    ElMessage.error('文档上传失败')
    options.onError?.(error as Parameters<NonNullable<typeof options.onError>>[0])
  } finally {
    loading.value = false
  }
}

function beforeUpload(file: File) {
  const allowTypes = ['.txt', '.md', '.pdf']
  const isAllowed = allowTypes.includes(getFileType(file.name))
  if (!isAllowed) {
    ElMessage.error('仅支持上传 .txt、.md、.pdf 文件')
  }
  return isAllowed
}
</script>

<template>
  <div class="document-page">
    <el-card shadow="never" class="page-card" v-loading="loading">
      <template #header>
        <div class="title">文档上传</div>
      </template>

      <el-upload
        drag
        action="#"
        accept=".txt,.md,.pdf"
        :show-file-list="false"
        :http-request="handleUpload"
        :before-upload="beforeUpload"
      >
        <div class="upload-content">
          <div class="upload-title">拖拽文件到这里，或点击选择文件</div>
          <div class="upload-desc">支持 PDF、TXT、Markdown，上传后自动切分并写入知识库。</div>
        </div>
      </el-upload>

      <el-alert
        v-if="lastResult"
        class="result-alert"
        type="success"
        show-icon
        :closable="false"
        :title="`上传成功：${lastResult.filename}，共 ${lastResult.chunkCount} 个 Chunk`"
      />
    </el-card>

    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="title">上传结果</div>
      </template>

      <el-table :data="records" stripe empty-text="暂无上传记录">
        <el-table-column prop="filename" label="文件名" min-width="220" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="chunkCount" label="Chunk 数量" width="130" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploadedAt" label="上传时间" width="220" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.document-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-card {
  border-radius: 8px;
}

.title {
  font-weight: 700;
  color: #111827;
}

.upload-content {
  padding: 18px;
}

.upload-title {
  font-size: 17px;
  font-weight: 700;
  color: #111827;
}

.upload-desc {
  margin-top: 8px;
  color: #6b7280;
}

.result-alert {
  margin-top: 18px;
}
</style>
