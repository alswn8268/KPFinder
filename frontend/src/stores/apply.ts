import { defineStore } from 'pinia'
import { ref } from 'vue'

import { applyPlan, buildPlan } from '@/api/apply'
import type { ApplyResponse, PlanItem } from '@/api/types'
import { useEditStore } from '@/stores/edit'
import { useScanStore } from '@/stores/scan'

export const useApplyStore = defineStore('apply', () => {
  const plan = ref<PlanItem[]>([])
  const planning = ref(false)
  const applying = ref(false)
  const lastResult = ref<ApplyResponse | null>(null)

  async function refreshPlan() {
    const scan = useScanStore()
    const edit = useEditStore()
    planning.value = true
    try {
      plan.value = await buildPlan(scan.root, edit.merged)
      return plan.value
    } finally {
      planning.value = false
    }
  }

  async function apply(note: string) {
    const scan = useScanStore()
    const edit = useEditStore()
    applying.value = true
    try {
      const result = await applyPlan(scan.root, edit.merged, scan.entries, note)
      lastResult.value = result
      return result
    } finally {
      applying.value = false
    }
  }

  function reset() {
    plan.value = []
    lastResult.value = null
  }

  return { plan, planning, applying, lastResult, refreshPlan, apply, reset }
})
