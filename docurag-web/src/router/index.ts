import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../views/Dashboard.vue'),
          meta: { title: '首页概览' },
        },
        {
          path: 'knowledge-base',
          name: 'KnowledgeBase',
          component: () => import('../views/KnowledgeBase.vue'),
          meta: { title: '知识库列表' },
        },
        {
          path: 'documents',
          name: 'DocumentManage',
          component: () => import('../views/DocumentManage.vue'),
          meta: { title: '文档管理' },
        },
        {
          path: 'chat',
          name: 'ChatPage',
          component: () => import('../views/ChatPage.vue'),
          meta: { title: '智能问答' },
        },
        {
          path: 'history',
          name: 'QaHistory',
          component: () => import('../views/QaHistory.vue'),
          meta: { title: '问答日志' },
        },
      ],
    },
  ],
})

export default router
