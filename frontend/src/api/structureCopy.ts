import { apiClient } from './client'
import type { FileEntry, StructureCopyResponse } from './types'

export async function copyStructureOnly(entries: FileEntry[], destRoot: string): Promise<StructureCopyResponse> {
  const { data } = await apiClient.post<StructureCopyResponse>('/structure/copy', {
    entries,
    dest_root: destRoot,
  })
  return data
}
