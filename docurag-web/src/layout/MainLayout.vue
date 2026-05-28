<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ChatDotRound,
  Collection,
  DataBoard,
  Document,
  Tickets,
} from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)

const menus = [
  { path: '/dashboard', label: '首页', icon: DataBoard },
  { path: '/knowledge-base', label: '知识库', icon: Collection },
  { path: '/documents', label: '文档管理', icon: Document },
  { path: '/chat', label: '智能问答', icon: ChatDotRound },
  { path: '/history', label: '问答日志', icon: Tickets },
]

function handleSelect(path: string) {
  router.push(path)
}
</script>

<template>
  <el-container class="admin-layout">
    <el-aside width="220px" class="sidebar">
      <div class="brand">
        <div class="brand-mark">D</div>
        <div>
          <div class="brand-name">DocuRAG</div>
          <div class="brand-subtitle">RAG v2 Console</div>
        </div>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="side-menu"
        router
        @select="handleSelect"
      >
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div>
          <h1>{{ appStore.title }}</h1>
          <p>{{ route.meta.title || '管理后台' }}</p>
        </div>
        <el-tag type="success" effect="light">Hybrid + Rerank</el-tag>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background: #f3f6fb;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  height: 76px;
  padding: 0 20px;
  border-bottom: 1px solid #eef2f7;
}

.brand-mark {
  display: grid;
  width: 38px;
  height: 38px;
  color: #ffffff;
  font-weight: 700;
  background: #2563eb;
  border-radius: 8px;
  place-items: center;
}

.brand-name {
  font-size: 17px;
  font-weight: 700;
  color: #111827;
}

.brand-subtitle {
  margin-top: 2px;
  font-size: 12px;
  color: #6b7280;
}

.side-menu {
  border-right: 0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 76px;
  padding: 0 28px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  letter-spacing: 0;
}

.header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.main {
  padding: 24px;
}
</style>
