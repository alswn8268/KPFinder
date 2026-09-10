import { apiClient } from './client'
import type { VersionInfo } from './types'

export async function listVersions(root: string): Promise<VersionInfo[]> {
  const { data } = await apiClient.get<VersionInfo[]>('/versions', { params: { root } })
  return data
}

export async function restoreVersion(root: string, versionId: string): Promise<{ restored_count: number }> {
  const { data } = await apiClient.post(`/versions/${encodeURIComponent(versionId)}/restore`, { root })
  return data
}
