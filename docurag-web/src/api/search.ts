import request, { type ApiResponse } from './request'
import type { RagChunk } from './chat'

export function keywordSearch(question: string) {
  return request.post<ApiResponse<RagChunk[]>>('/reg/key-word-search', { question })
}

export function rerankSearch(question: string) {
  return request.post<ApiResponse<{ question: string; results: RagChunk[] }>>(
    '/reg/rerank-search',
    { question },
  )
}
