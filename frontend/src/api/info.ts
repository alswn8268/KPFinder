import { apiClient } from './client'
import type { InfoResponse } from './types'

export async function getInfo(): Promise<InfoResponse> {
  const { data } = await apiClient.get<InfoResponse>('/info')
  return data
}
