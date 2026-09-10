import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { validateAssignments } from '@/api/edit'
import type { AssignmentInfo, OverrideInfo, RejectedItem } from '@/api/types'
import { useClassificationStore } from '@/stores/classification'
import { useScanStore } from '@/stores/scan'

export interface EditHistoryEntry {
  src: string
  aiDst: string
  userDst: string
  at: string
}

export const useEditStore = defineStore('edit', () => {
  const overrides = ref<Record<string, OverrideInfo>>({})
  const history = ref<EditHistoryEntry[]>([])

  const valid = ref<Record<string, AssignmentInfo>>({})
  const merged = ref<Record<string, AssignmentInfo>>({})
  const rejected = ref<RejectedItem[]>([])
  const excluded = ref<string[]>([])
  const finalState = ref<Record<string, string>[]>([])
  const treeBefore = ref('')
  const treeAfter = ref('')
  const validating = ref(false)

  const modifiedCount = computed(() => Object.keys(overrides.value).length)

  async function refresh() {
    const scan = useScanStore()
    const classification = useClassificationStore()
    validating.value = true
    try {
      const result = await validateAssignments(
        scan.entries,
        scan.root,
        classification.assignments,
        overrides.value,
      )
      valid.value = result.valid
      merged.value = result.merged
      rejected.value = result.rejected
      excluded.value = result.excluded
      finalState.value = result.final_state
      treeBefore.value = result.tree_before
      treeAfter.value = result.tree_after
      return result
    } finally {
      validating.value = false
    }
  }

  function setOverride(src: string, dst: string | null, excludedFlag: boolean) {
    const original = valid.value[src]
    const aiDst = original?.dst ?? ''
    const isNoop = !excludedFlag && (dst === null || dst === aiDst)
    if (isNoop) {
      delete overrides.value[src]
    } else {
      overrides.value[src] = { dst, excluded: excludedFlag }
      history.value.push({
        src,
        aiDst,
        userDst: excludedFlag ? '(제외)' : dst ?? aiDst,
        at: new Date().toLocaleString('ko-KR'),
      })
    }
  }

  function clearOverride(src: string) {
    delete overrides.value[src]
  }

  function bulkSetDestination(srcs: string[], targetFolder: string) {
    for (const src of srcs) {
      const original = valid.value[src]
      if (!original) continue
      const filename = original.dst.split('/').pop() ?? src.split('/').pop() ?? src
      setOverride(src, `${targetFolder}/${filename}`, false)
    }
  }

  function resetToSuggestion(srcs: string[]) {
    for (const src of srcs) clearOverride(src)
  }

  function reset() {
    overrides.value = {}
    history.value = []
    valid.value = {}
    merged.value = {}
    rejected.value = []
    excluded.value = []
    finalState.value = []
    treeBefore.value = ''
    treeAfter.value = ''
  }

  return {
    overrides,
    history,
    valid,
    merged,
    rejected,
    excluded,
    finalState,
    treeBefore,
    treeAfter,
    validating,
    modifiedCount,
    refresh,
    setOverride,
    clearOverride,
    bulkSetDestination,
    resetToSuggestion,
    reset,
  }
})
