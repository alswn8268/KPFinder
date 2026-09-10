import { defineStore } from 'pinia'
import { ref } from 'vue'

import { checkEnvironment } from '@/api/env'
import type { EnvItem } from '@/api/types'

export const useEnvStore = defineStore('env', () => {
  const items = ref<EnvItem[]>([])
  const hasBlockingError = ref(false)
  const checked = ref(false)
  const checking = ref(false)

  async function check(root = '', model?: string) {
    checking.value = true
    try {
      const result = await checkEnvironment(root, model)
      items.value = result.items
      hasBlockingError.value = result.has_blocking_error
      checked.value = true
      return result
    } finally {
      checking.value = false
    }
  }

  function ollamaConnected(): boolean {
    return items.value.find((i) => i.item === 'Ollama 실행 여부')?.status === '정상'
  }

  return { items, hasBlockingError, checked, checking, check, ollamaConnected }
})
