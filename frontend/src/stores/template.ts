import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  getDefaultTemplate,
  importTemplate,
  listSampleTemplates,
  listTemplates,
  saveTemplate,
  templateFromCurrentStructure,
  templateFromFolderList,
} from '@/api/templates'
import type { FileEntry, OrgTemplate } from '@/api/types'

export const useTemplateStore = defineStore('template', () => {
  const active = ref<OrgTemplate | null>(null)
  const saved = ref<OrgTemplate[]>([])
  const samples = ref<OrgTemplate[]>([])
  const loading = ref(false)

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

  return {
    active,
    saved,
    samples,
    loading,
    loadDefault,
    refreshSaved,
    loadSamples,
    importFromJson,
    fromCurrentStructure,
    fromFolderList,
    persist,
    selectSaved,
  }
})
