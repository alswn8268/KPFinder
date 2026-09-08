import { apiClient } from './client'
import type { ModelsResponse } from './types'

export async function listInstalledModels(): Promise<ModelsResponse> {
  const { data } = await apiClient.get<ModelsResponse>('/models')
  return data
}
