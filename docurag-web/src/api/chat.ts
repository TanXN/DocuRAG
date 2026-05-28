import request, { type ApiResponse } from './request'

export interface ChunkMetadata {
  file_name?: string
  file_type?: string
  page?: number | string
  chunk_index?: number | string
}

export interface RagChunk {
  source_id?: string
  document?: string
  metadata?: ChunkMetadata
  retrieval_type?: string
  distance?: number
  bm25_score?: number
  rerank_score?: number
}

export interface ChatResult {
  question: string
  answer: string
  chunks: RagChunk[]
}

export function askQuestion(question: string) {
  return request.post<ApiResponse<ChatResult>>('/reg/chat', { question })
}
