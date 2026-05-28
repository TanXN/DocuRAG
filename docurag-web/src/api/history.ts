import request, { type ApiResponse } from './request'
import type { RagChunk } from './chat'

export interface HistoryItem {
  id: number
  question: string
  answer: string
  chunks?: RagChunk[] | string
  created_at: string
}

export function getHistory(limit = 50) {
  return request.get<ApiResponse<HistoryItem[]>>('/reg/rag-history', {
    params: { limit },
  })
}
