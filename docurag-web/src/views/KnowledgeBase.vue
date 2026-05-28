<script setup lang="ts">
const tableData = [
  {
    name: '默认知识库',
    description: 'DocuRAG 默认测试知识库',
    documentCount: 1,
    chunkCount: '-',
    createdAt: '-',
  },
]
</script>

<template>
  <el-card shadow="never" class="page-card">
    <template #header>
      <div class="card-header">
        <div>
          <div class="title">知识库列表</div>
          <div class="subtitle">当前后端暂无知识库列表接口，先展示默认知识库。</div>
        </div>
        <el-button type="primary" disabled>新建知识库</el-button>
      </div>
    </template>

    <el-table :data="tableData" stripe>
      <el-table-column prop="name" label="知识库名称" min-width="160" />
      <el-table-column prop="description" label="描述" min-width="240" />
      <el-table-column prop="documentCount" label="文档数量" width="120" />
      <el-table-column prop="chunkCount" label="Chunk 数量" width="130" />
      <el-table-column prop="createdAt" label="创建时间" width="140" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default>
          <el-button size="small" type="primary" plain>查看</el-button>
          <el-button size="small" disabled>配置</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<style scoped>
.page-card {
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
</style>
