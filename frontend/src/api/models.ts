import { apiClient } from './client'
import type { ModelsResponse, PullProgressEvent, RecommendedModelInfo } from './types'

export async function listInstalledModels(): Promise<ModelsResponse> {
  const { data } = await apiClient.get<ModelsResponse>('/models')
  return data
}

export async function listRecommendedModels(): Promise<RecommendedModelInfo[]> {
  const { data } = await apiClient.get<RecommendedModelInfo[]>('/models/recommended')
  return data
}

/**
 * 모델 다운로드는 수 분 걸릴 수 있는 스트리밍 응답이라 axios 대신 fetch를 직접 써서
 * 응답 바디를 한 줄(NDJSON)씩 읽어가며 진행 상황을 콜백으로 넘긴다.
 */
export async function pullModel(model: string, onProgress: (evt: PullProgressEvent) => void): Promise<void> {
  const resp = await fetch('/api/models/pull', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model }),
  })
  if (!resp.ok || !resp.body) {
    throw new Error('다운로드를 시작할 수 없습니다.')
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.trim()) continue
      const evt = JSON.parse(line) as PullProgressEvent
      onProgress(evt)
      if (evt.status === 'error') throw new Error(evt.error || '다운로드 중 오류가 발생했습니다.')
    }
  }
  if (buffer.trim()) {
    const evt = JSON.parse(buffer) as PullProgressEvent
    onProgress(evt)
    if (evt.status === 'error') throw new Error(evt.error || '다운로드 중 오류가 발생했습니다.')
  }
}
