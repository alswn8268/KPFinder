import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  getDefaultTemplate,
  importTemplate,
  listSampleTemplates,
  listTemplates,
  saveTemplate,
  suggestStructure,
  templateFromAiProposal,
  templateFromCurrentStructure,
  templateFromFolderList,
} from '@/api/templates'
import type { FileEntry, OrgTemplate, SuggestStructureResponse } from '@/api/types'

export const useTemplateStore = defineStore('template', () => {
  const active = ref<OrgTemplate | null>(null)
  const saved = ref<OrgTemplate[]>([])
  const samples = ref<OrgTemplate[]>([])
  const loading = ref(false)
  const suggestion = ref<SuggestStructureResponse | null>(null)
  const suggesting = ref(false)

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
   * suggestion에 담겨 사람이 검토한 뒤 fromAiProposal()로 넘어가야 한다. */
  async function suggestNewStructure(entries: FileEntry[], model: string, hint = '') {
    suggesting.value = true
    try {
      suggestion.value = await suggestStructure(entries, model, hint)
      return suggestion.value
    } finally {
      suggesting.value = false
    }
  }

  async function fromAiProposal(name: string) {
    if (!suggestion.value) return
    active.value = await templateFromAiProposal(suggestion.value.categories, name)
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
    loadDefault,
    refreshSaved,
    loadSamples,
    importFromJson,
    fromCurrentStructure,
    fromFolderList,
    persist,
    selectSaved,
    suggestNewStructure,
    fromAiProposal,
    clearSuggestion,
  }
})
