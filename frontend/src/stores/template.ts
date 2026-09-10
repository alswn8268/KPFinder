import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  getDefaultTemplate,
  importTemplate,
  listSampleTemplates,
  listTemplates,
  saveTemplate,
  suggestStructure,
  suggestStructureUpdate,
  templateFromAiProposal,
  templateFromCurrentStructure,
  templateFromFolderList,
  templateFromHybridProposal,
} from '@/api/templates'
import type { FileEntry, OrgTemplate, SuggestStructureResponse } from '@/api/types'

export type SuggestionMode = 'free' | 'hybrid'

export const useTemplateStore = defineStore('template', () => {
  const active = ref<OrgTemplate | null>(null)
  const saved = ref<OrgTemplate[]>([])
  const samples = ref<OrgTemplate[]>([])
  const loading = ref(false)
  const suggestion = ref<SuggestStructureResponse | null>(null)
  const suggesting = ref(false)
  // "다시 제안받기"에서 같은 조건으로 재시도할 수 있도록, 마지막 제안을 만든 조건을
  // 기억해 둔다(하이브리드 모드는 어떤 템플릿을 기준으로 만들었는지도 필요하다).
  const suggestionMode = ref<SuggestionMode>('free')
  const suggestionHint = ref('')
  const suggestionBaseTemplate = ref<OrgTemplate | null>(null)

  async function loadDefault() {
    active.value = await getDefaultTemplate()
    return active.value
  }

  async function refreshSaved() {
    saved.value = await listTemplates()
    return saved.value
  }

  async function loadSamples() {
    samples.value = await listSampleTemplates()
    return samples.value
  }

  async function importFromJson(jsonText: string) {
    active.value = await importTemplate(jsonText)
    return active.value
  }

  async function fromCurrentStructure(entries: FileEntry[], name: string) {
    active.value = await templateFromCurrentStructure(entries, name)
    return active.value
  }

  async function fromFolderList(text: string, name: string) {
    active.value = await templateFromFolderList(text, name)
    return active.value
  }

  async function persist() {
    if (!active.value) return
    await saveTemplate(active.value)
    await refreshSaved()
  }

  function selectSaved(template: OrgTemplate) {
    active.value = template
  }

  /** AI가 새 폴더 구조를 자유롭게 제안하게 한다 — 결과는 바로 템플릿이 되지 않고
   * suggestion에 담겨 사람이 검토한 뒤 fromAiProposal()로 넘어가야 한다. 파일이 많으면
   * 서버(organizer.suggest_new_structure)가 자동으로 나눠 호출한다. */
  async function suggestNewStructure(
    entries: FileEntry[],
    model: string,
    hint = '',
    adjustment = '',
  ) {
    suggesting.value = true
    try {
      suggestionMode.value = 'free'
      suggestionHint.value = hint
      suggestionBaseTemplate.value = null
      suggestion.value = await suggestStructure(entries, model, hint, adjustment)
      return suggestion.value
    } finally {
      suggesting.value = false
    }
  }

  /** 하이브리드 모드 — baseTemplate의 폴더는 유지하고, 부족한 카테고리만 AI가 추가로
   * 제안하게 한다. suggestNewStructure()와 마찬가지로 결과는 검토 후 fromAiProposal()로
   * 넘어가야 한다. */
  async function suggestHybridStructure(
    entries: FileEntry[],
    baseTemplate: OrgTemplate,
    model: string,
    hint = '',
    adjustment = '',
  ) {
    suggesting.value = true
    try {
      suggestionMode.value = 'hybrid'
      suggestionHint.value = hint
      suggestionBaseTemplate.value = baseTemplate
      suggestion.value = await suggestStructureUpdate(entries, baseTemplate, model, hint, adjustment)
      return suggestion.value
    } finally {
      suggesting.value = false
    }
  }

  /** "AI 제안 다시 받기" — 마지막 제안과 같은 모드·힌트·기준 템플릿으로 재시도한다.
   * adjustment('fewer'|'more')를 주면 카테고리를 줄이거나 늘리는 방향으로 다시 받는다. */
  async function retrySuggestion(entries: FileEntry[], model: string, adjustment = '') {
    if (suggestionMode.value === 'hybrid' && suggestionBaseTemplate.value) {
      return suggestHybridStructure(entries, suggestionBaseTemplate.value, model, suggestionHint.value, adjustment)
    }
    return suggestNewStructure(entries, model, suggestionHint.value, adjustment)
  }

  async function fromAiProposal(name: string) {
    if (!suggestion.value) return
    if (suggestionMode.value === 'hybrid' && suggestionBaseTemplate.value) {
      active.value = await templateFromHybridProposal(
        suggestionBaseTemplate.value,
        suggestion.value.categories,
        name,
      )
    } else {
      active.value = await templateFromAiProposal(suggestion.value.categories, name)
    }
    suggestion.value = null
    return active.value
  }

  function clearSuggestion() {
    suggestion.value = null
  }

  return {
    active,
    saved,
    samples,
    loading,
    suggestion,
    suggesting,
    suggestionMode,
    loadDefault,
    refreshSaved,
    loadSamples,
    importFromJson,
    fromCurrentStructure,
    fromFolderList,
    persist,
    selectSaved,
    suggestNewStructure,
    suggestHybridStructure,
    retrySuggestion,
    fromAiProposal,
    clearSuggestion,
  }
})
