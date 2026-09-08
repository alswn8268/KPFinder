import { defineStore } from 'pinia'
import { ref } from 'vue'

import { classifyEntries, findSimilarDocuments, summarizeEntries } from '@/api/classify'
import { getInfo } from '@/api/info'
import { listInstalledModels } from '@/api/models'
import type {
  AssignmentInfo,
  FileEntry,
  KeywordRule,
  OllamaModelInfo,
  OrgTemplate,
  SimilarPair,
} from '@/api/types'

export const useClassificationStore = defineStore('classification', () => {
  const model = ref('')
  const useAi = ref(true)
  const summarizing = ref(false)
  const classifying = ref(false)
  const categories = ref<string[]>([])
  const assignments = ref<Record<string, AssignmentInfo>>({})
  const notes = ref('')
  const aiFailed = ref(false)
  const errorDetail = ref('')
  const similarDocs = ref<SimilarPair[]>([])
  const hasResult = ref(false)

  const availableModels = ref<OllamaModelInfo[]>([])
  const modelsLoading = ref(false)
  const modelPickedByUser = ref(false)

  async function loadDefaultModel() {
    if (model.value) return
    const info = await getInfo()
    model.value = info.default_model
  }

  /** 실제로 이 PC에 설치된 모델 목록을 불러온다. 사용자가 아직 직접 고르지 않았다면,
   * 기본 모델이 설치되어 있으면 그걸, 아니면 가장 가벼운(용량 작은) 모델을 자동 선택한다 —
   * 사양을 잘 모르는 사용자도 일단 안전하게 시작할 수 있도록. */
  async function loadAvailableModels() {
    modelsLoading.value = true
    try {
      const result = await listInstalledModels()
      availableModels.value = result.models
      if (!modelPickedByUser.value && result.models.length > 0) {
        const hasDefault = result.models.some((m) => m.name === model.value)
        if (!hasDefault) {
          model.value = result.models[0].name // 크기순 정렬이라 첫 번째가 가장 가볍다
        }
      }
      return result
    } finally {
      modelsLoading.value = false
    }
  }

  function selectModel(name: string) {
    model.value = name
    modelPickedByUser.value = true
  }

  async function runClassification(
    entries: FileEntry[],
    root: string,
    template: OrgTemplate,
    effectiveUseAi: boolean,
    userRules: KeywordRule[] = [],
  ) {
    classifying.value = true
    try {
      if (effectiveUseAi) {
        summarizing.value = true
        try {
          const summarized = await summarizeEntries(entries, root, model.value)
          summarized.forEach((updated, i) => Object.assign(entries[i], updated))
        } finally {
          summarizing.value = false
        }
      }

      const result = await classifyEntries(entries, template, model.value, effectiveUseAi, userRules)
      categories.value = result.categories
      assignments.value = result.assignments
      notes.value = result.notes
      aiFailed.value = result.ai_failed
      errorDetail.value = result.error_detail
      similarDocs.value = effectiveUseAi ? await findSimilarDocuments(entries) : []
      hasResult.value = true
      return result
    } finally {
      classifying.value = false
    }
  }

  function reset() {
    categories.value = []
    assignments.value = {}
    notes.value = ''
    aiFailed.value = false
    errorDetail.value = ''
    similarDocs.value = []
    hasResult.value = false
  }

  return {
    model,
    useAi,
    summarizing,
    classifying,
    categories,
    assignments,
    notes,
    aiFailed,
    errorDetail,
    similarDocs,
    hasResult,
    availableModels,
    modelsLoading,
    loadDefaultModel,
    loadAvailableModels,
    selectModel,
    runClassification,
    reset,
  }
})
