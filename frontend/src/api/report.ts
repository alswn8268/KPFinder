import { apiClient } from './client'
import type { DuplicateGroup, EnvItem, FileEntry, SimilarPair } from './types'
import { downloadBlob, timestampedFilename } from '@/utils/download'

export interface ReportPayload {
  entries: FileEntry[]
  duplicate_groups: DuplicateGroup[]
  proposal: Record<string, unknown>
  similar_docs: SimilarPair[]
  final_state: Record<string, string>[]
  env_items: EnvItem[]
  model: string
  template_name: string
  template_version: string
}

export async function downloadJsonReport(payload: ReportPayload) {
  const { data } = await apiClient.post('/report/json', payload, { responseType: 'blob' })
  downloadBlob(data, timestampedFilename('folder_organize_report', 'json'))
}

export async function downloadExcelReport(payload: ReportPayload) {
  const { data } = await apiClient.post('/report/excel', payload, { responseType: 'blob' })
  downloadBlob(data, timestampedFilename('folder_organize_report', 'xlsx'))
}

export async function fetchHtmlReport(payload: ReportPayload): Promise<string> {
  const { data } = await apiClient.post('/report/html', payload, {
    responseType: 'text',
    transformResponse: (v) => v,
  })
  return data as unknown as string
}

export function openHtmlReportInNewTab(html: string) {
  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
}
