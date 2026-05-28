import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    title: 'DocuRAG 企业知识库问答系统',
  }),
})
