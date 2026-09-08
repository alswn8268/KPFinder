import { apiClient } from './client'
import type { ScanOptions, ScanResponse } from './types'

export async function scanFolder(root: string, options?: Partial<ScanOptions>): Promise<ScanResponse> {
  const { data } = await apiClient.post<ScanResponse>('/scan', {
    root,
    exclude_dirs: options?.exclude_dirs ?? [],
    exclude_exts: options?.exclude_exts ?? [],
    include_hidden: options?.include_hidden ?? false,
    max_file_size_mb: options?.max_file_size_mb ?? null,
  })
  return data
}
