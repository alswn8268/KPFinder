import { apiClient } from './client'
import type { FileEntry, OrgTemplate } from './types'

export async function listTemplates(): Promise<OrgTemplate[]> {
  const { data } = await apiClient.get<OrgTemplate[]>('/templates')
  return data
}

export async function getDefaultTemplate(): Promise<OrgTemplate> {
  const { data } = await apiClient.get<OrgTemplate>('/templates/default')
  return data
}

export async function listSampleTemplates(): Promise<OrgTemplate[]> {
  const { data } = await apiClient.get<OrgTemplate[]>('/templates/samples')
  return data
}

export async function importTemplate(jsonText: string): Promise<OrgTemplate> {
  const { data } = await apiClient.post<OrgTemplate>('/templates/import', { json_text: jsonText })
  return data
}

export async function saveTemplate(template: OrgTemplate): Promise<{ path: string }> {
  const { data } = await apiClient.post('/templates/save', { template })
  return data
}

export async function exportTemplate(template: OrgTemplate): Promise<string> {
  const { data } = await apiClient.post('/templates/export', template, {
    responseType: 'text',
    transformResponse: (v) => v,
  })
  return data as unknown as string
}

export async function templateFromCurrentStructure(entries: FileEntry[], name: string): Promise<OrgTemplate> {
  const { data } = await apiClient.post<OrgTemplate>('/templates/from-current-structure', { entries, name })
  return data
}

export async function templateFromFolderList(
  text: string,
  name: string,
  keepUnclassified = true,
): Promise<OrgTemplate> {
  const { data } = await apiClient.post<OrgTemplate>('/templates/from-folder-list', {
    text,
    name,
    keep_unclassified: keepUnclassified,
  })
  return data
}
