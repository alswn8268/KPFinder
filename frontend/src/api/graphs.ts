import { apiClient } from './client'
import type { FileEntry, GraphData, TreeNode } from './types'

export async function fetchContentGraph(
  entries: FileEntry[],
  minScore = 0.35,
  hideIsolated = true,
): Promise<GraphData> {
  const { data } = await apiClient.post<GraphData>('/graphs/content', {
    entries,
    min_score: minScore,
    hide_isolated: hideIsolated,
  })
  return data
}

export async function fetchDirectoryTree(entries: FileEntry[]): Promise<TreeNode> {
  const { data } = await apiClient.post<TreeNode>('/graphs/directory-tree', { entries })
  return data
}

export async function fetchDirectoryRelationGraph(entries: FileEntry[], minScore = 0.4): Promise<GraphData> {
  const { data } = await apiClient.post<GraphData>('/graphs/directory-relation', {
    entries,
    min_score: minScore,
  })
  return data
}
