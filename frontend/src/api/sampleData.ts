import { apiClient } from './client'
import type { SampleDataResponse } from './types'

export async function generateSampleData(outputDir?: string, force = false): Promise<SampleDataResponse> {
  const { data } = await apiClient.post<SampleDataResponse>('/sample-data/generate', {
    output_dir: outputDir || null,
    force,
  })
  return data
}
