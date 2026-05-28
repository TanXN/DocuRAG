import axios, { type AxiosResponse } from 'axios'

export interface ApiResponse<T = unknown> {
  code: number
  msg?: string
  message?: string
  data: T
}

const request = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => response,
  (error) => Promise.reject(error),
)

export default request
