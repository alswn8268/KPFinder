import { apiClient } from './client'
import type { ApplyResponse, AssignmentInfo, FileEntry, PlanItem } from './types'

export async function buildPlan(
  root: string,
  assignments: Record<string, AssignmentInfo>,
): Promise<PlanItem[]> {
  const { data } = await apiClient.post<{ plan: PlanItem[] }>('/plan', { root, assignments })
  return data.plan
}

export async function applyPlan(
  root: string,
  assignments: Record<string, AssignmentInfo>,
  entries: FileEntry[],
  note = '',
): Promise<ApplyResponse> {
  const { data } = await apiClient.post<ApplyResponse>('/apply', { root, assignments, entries, note })
  return data
}
