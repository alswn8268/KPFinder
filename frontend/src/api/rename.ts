import { apiClient } from './client'
import type { AssignmentInfo, FileEntry, RenamePreviewRow, RenameRule } from './types'

export async function previewRename(entries: FileEntry[], rule: RenameRule): Promise<RenamePreviewRow[]> {
  const { data } = await apiClient.post<RenamePreviewRow[]>('/rename/preview', { entries, rule })
  return data
}

export async function buildRenameAssignments(
  entries: FileEntry[],
  rule: RenameRule,
): Promise<Record<string, AssignmentInfo>> {
  const { data } = await apiClient.post<{ assignments: Record<string, AssignmentInfo> }>(
    '/rename/assignments',
    { entries, rule },
  )
  return data.assignments
}
