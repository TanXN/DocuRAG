import request, { type ApiResponse } from './request'

export interface UploadResult {
  filename: string
  chunk_count: number
}

export function uploadDocument(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  return request.post<ApiResponse<UploadResult>>('/rag/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
