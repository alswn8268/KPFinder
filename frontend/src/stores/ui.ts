import { defineStore } from 'pinia'
import { ref } from 'vue'

import { applyAccentColor, DEFAULT_ACCENT } from '@/utils/colorRamp'

export interface Toast {
  id: number
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
}

let nextId = 1

export const useUiStore = defineStore('ui', () => {
  const toasts = ref<Toast[]>([])
  const pointColor = ref(localStorage.getItem('pointColor') || DEFAULT_ACCENT)
  const globalLoading = ref(false)

  function pushToast(message: string, type: Toast['type'] = 'info', durationMs = 4200) {
    const id = nextId++
    toasts.value.push({ id, type, message })
    window.setTimeout(() => dismissToast(id), durationMs)
  }

  function dismissToast(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function setPointColor(hex: string) {
    pointColor.value = hex
    localStorage.setItem('pointColor', hex)
    applyAccentColor(hex)
  }

  applyAccentColor(pointColor.value)

  return { toasts, pointColor, globalLoading, pushToast, dismissToast, setPointColor }
})
