import { apiClient } from './client'
import type { EnvCheckResponse } from './types'

export async function checkEnvironment(root = '', model?: string): Promise<EnvCheckResponse> {
  const { data } = await apiClient.get<EnvCheckResponse>('/env/check', { params: { root, model } })
  return data
}
