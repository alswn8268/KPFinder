import { apiClient } from './client'
import type { CacheInfo } from './types'

export async function getCacheInfo(root: string): Promise<CacheInfo> {
  const { data } = await apiClient.get<CacheInfo>('/cache/info', { params: { root } })
  return data
}

export async function clearCurrentCache(root: string): Promise<{ cleared: boolean }> {
  const { data } = await apiClient.delete('/cache/current', { params: { root } })
  return data
}

export async function clearAllCaches(): Promise<{ cleared_count: number }> {
  const { data } = await apiClient.delete('/cache/all')
  return data
}
