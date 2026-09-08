import { apiClient } from './client'
import type { ClassifyResponse, FileEntry, KeywordRule, OrgTemplate, SimilarPair } from './types'

export async function summarizeEntries(entries: FileEntry[], root: string, model: string): Promise<FileEntry[]> {
  const { data } = await apiClient.post<{ entries: FileEntry[] }>('/summarize', { entries, root, model })
  return data.entries
}

export async function classifyEntries(
  entries: FileEntry[],
  template: OrgTemplate,
  model: string,
  useAi: boolean,
  userRules: KeywordRule[] = [],
): Promise<ClassifyResponse> {
  const { data } = await apiClient.post<ClassifyResponse>('/classify', {
    entries,
    template,
    model,
    use_ai: useAi,
    user_rules: userRules,
  })
  return data
}

export async function findSimilarDocuments(entries: FileEntry[]): Promise<SimilarPair[]> {
  const { data } = await apiClient.post<SimilarPair[]>('/similar', { entries })
  return data
}
