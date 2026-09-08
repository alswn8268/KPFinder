import axios from 'axios'

// 실제 Ollama 리허설 실측: 폴더 구조 제안(/classify)은 파일 10개 기준 약 258초가 걸렸다
// (app/llm_client.py의 STRUCTURE_TIMEOUT=600초와 맞춤). 백엔드가 먼저 타임아웃되도록
// 프런트엔드 쪽은 그보다 넉넉하게 잡아 둘 다 같은 순간에 끊기는 경합을 피한다.
const LONG_RUNNING_TIMEOUT_MS = 15 * 60 * 1000

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30_000,
})

apiClient.interceptors.request.use((config) => {
  if (config.url?.startsWith('/summarize') || config.url?.startsWith('/classify')) {
    config.timeout = LONG_RUNNING_TIMEOUT_MS
  }
  return config
})

export type ApiErrorListener = (message: string) => void
let errorListener: ApiErrorListener | null = null

export function onApiError(listener: ApiErrorListener) {
  errorListener = listener
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail =
      error?.response?.data?.detail ??
      error?.message ??
      '알 수 없는 오류가 발생했습니다.'
    const message = Array.isArray(detail) ? detail.map((d: any) => d.msg ?? d).join(', ') : detail
    errorListener?.(String(message))
    return Promise.reject(error)
  },
)
