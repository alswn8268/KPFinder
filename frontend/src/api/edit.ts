import { apiClient } from './client'
import type { AssignmentInfo, FileEntry, OverrideInfo, ValidateResponse } from './types'

export async function validateAssignments(
  entries: FileEntry[],
  root: string,
  assignments: Record<string, AssignmentInfo>,
  overrides: Record<string, OverrideInfo> = {},
): Promise<ValidateResponse> {
  const { data } = await apiClient.post<ValidateResponse>('/assignments/validate', {
    entries,
    root,
    assignments,
    overrides,
  })
  return data
}
