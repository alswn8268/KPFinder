import { apiClient } from './client'
import type { SampleDataResponse, SampleDatasetInfo } from './types'

export async function listSampleDatasets(): Promise<SampleDatasetInfo[]> {
  const { data } = await apiClient.get<SampleDatasetInfo[]>('/sample-data/datasets')
  return data
}

export async function generateSampleData(
  outputDir?: string,
  force = false,
  dataset = 'general_office',
): Promise<SampleDataResponse> {
  const { data } = await apiClient.post<SampleDataResponse>('/sample-data/generate', {
    output_dir: outputDir || null,
    force,
    dataset,
  })
  return data
}
