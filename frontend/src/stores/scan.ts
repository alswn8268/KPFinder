import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { scanFolder } from '@/api/scan'
import type { DuplicateGroup, FileEntry, ScanErrorItem, ScanOptions } from '@/api/types'

export const useScanStore = defineStore('scan', () => {
  const root = ref('')
  const entries = ref<FileEntry[]>([])
  const duplicateGroups = ref<DuplicateGroup[]>([])
  const scanErrors = ref<ScanErrorItem[]>([])
  const scanning = ref(false)
  const options = ref<ScanOptions>({
    exclude_dirs: [],
    exclude_exts: [],
    include_hidden: false,
    max_file_size_mb: null,
  })

  const hasScanned = computed(() => entries.value.length > 0)
  const totalFiles = computed(() => entries.value.length)

  async function scan(path: string) {
    scanning.value = true
    try {
      const result = await scanFolder(path, options.value)
      root.value = result.scan_root
      entries.value = result.entries
      duplicateGroups.value = result.duplicate_groups
      scanErrors.value = result.errors
      return result
    } finally {
      scanning.value = false
    }
  }

  function updateEntry(relativePath: string, patch: Partial<FileEntry>) {
    const target = entries.value.find((e) => e.relative_path === relativePath)
    if (target) Object.assign(target, patch)
  }

  function reset() {
    root.value = ''
    entries.value = []
    duplicateGroups.value = []
    scanErrors.value = []
  }

  return {
    root,
    entries,
    duplicateGroups,
    scanErrors,
    scanning,
    options,
    hasScanned,
    totalFiles,
    scan,
    updateEntry,
    reset,
  }
})
