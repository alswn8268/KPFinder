import { defineStore } from 'pinia'
import { ref } from 'vue'

import { listVersions, restoreVersion } from '@/api/versions'
import type { VersionInfo } from '@/api/types'

export const useVersionsStore = defineStore('versions', () => {
  const versions = ref<VersionInfo[]>([])
  const loading = ref(false)
  const restoring = ref<string | null>(null)

  async function fetch(root: string) {
    loading.value = true
    try {
      versions.value = await listVersions(root)
      return versions.value
    } finally {
      loading.value = false
    }
  }

  async function restore(root: string, versionId: string) {
    restoring.value = versionId
    try {
      const result = await restoreVersion(root, versionId)
      await fetch(root)
      return result
    } finally {
      restoring.value = null
    }
  }

  return { versions, loading, restoring, fetch, restore }
})
