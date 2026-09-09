<script setup lang="ts">
import { ref } from 'vue'

import { exportTemplate } from '@/api/templates'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import { downloadBlob } from '@/utils/download'
import { useScanStore } from '@/stores/scan'
import { useTemplateStore } from '@/stores/template'
import { useUiStore } from '@/stores/ui'

const template = useTemplateStore()
const scan = useScanStore()
const ui = useUiStore()

const importText = ref('')
const folderListText = ref('')
const folderListName = ref('내 템플릿')
const structureName = ref('')

if (!template.active) template.loadDefault()
template.refreshSaved()
template.loadSamples()

function onSelectSample(t: (typeof template.samples)[number]) {
  template.selectSaved(t)
  ui.pushToast(`샘플 템플릿 '${t.name}'을(를) 적용했습니다.`, 'success')
}

async function onLoadDefault() {
  await template.loadDefault()
  ui.pushToast('기본 템플릿으로 되돌렸습니다.', 'success')
}

async function onImport() {
  if (!importText.value.trim()) return
  try {
    await template.importFromJson(importText.value)
    ui.pushToast(`템플릿 '${template.active?.name}'을(를) 불러왔습니다.`, 'success')
    importText.value = ''
  } catch {
    ui.pushToast('템플릿을 읽을 수 없습니다.', 'error')
  }
}

async function onFileImport(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  importText.value = await file.text()
  await onImport()
}

async function onExport() {
  if (!template.active) return
  const text = await exportTemplate(template.active)
  downloadBlob(new Blob([text], { type: 'application/json' }), `${template.active.name}.json`)
}

async function onFromCurrentStructure() {
  if (!scan.hasScanned) {
    ui.pushToast('먼저 폴더를 스캔하세요.', 'warning')
    return
  }
  const name = structureName.value.trim() || '현재 구조 템플릿'
  await template.fromCurrentStructure(scan.entries, name)
  ui.pushToast('현재 폴더 구조를 템플릿으로 만들었습니다.', 'success')
}

async function onFromFolderList() {
  try {
    await template.fromFolderList(folderListText.value, folderListName.value || '내 템플릿')
    ui.pushToast(`템플릿 '${template.active?.name}'을(를) 만들었습니다.`, 'success')
  } catch {
    ui.pushToast('폴더 목록이 비어 있습니다. 한 줄에 하나씩 입력하세요.', 'error')
  }
}

async function onSave() {
  await template.persist()
  ui.pushToast('템플릿을 저장했습니다.', 'success')
}
</script>

<template>
  <div class="template-panel">
    <BaseCard>
      <template #header>현재 템플릿</template>
      <p class="template-panel__current">
        <strong>{{ template.active?.name ?? '기본 조직 템플릿' }}</strong>
        <span class="muted">버전 {{ template.active?.version }}</span>
      </p>
      <pre class="template-panel__folders">{{ (template.active?.folders ?? []).map((f) => f.path).join('\n') }}</pre>
      <div class="template-panel__actions">
        <BaseButton variant="secondary" size="sm" @click="onLoadDefault">기본 템플릿으로 되돌리기</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="onExport">내보내기(JSON 다운로드)</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="onSave">저장</BaseButton>
      </div>
    </BaseCard>

    <BaseCard v-if="template.samples.length">
      <template #header>🏢 부서별 샘플 템플릿</template>
      <p class="muted template-panel__samples-intro">
        시연용으로 미리 만들어 둔 부서별 표준 폴더 체계입니다. 클릭 한 번으로 현재
        템플릿으로 적용해 볼 수 있습니다.
      </p>
      <div class="template-panel__samples">
        <button
          v-for="t in template.samples"
          :key="t.name"
          type="button"
          class="template-panel__sample-card"
          :class="{ 'template-panel__sample-card--active': template.active?.name === t.name }"
          @click="onSelectSample(t)"
        >
          <strong>{{ t.name }}</strong>
          <span class="template-panel__sample-count">{{ t.folders.length }}개 폴더 · 규칙 {{ t.keyword_rules.length }}개</span>
          <span class="template-panel__sample-folders">{{ t.folders.slice(0, 4).map((f) => f.path).join(' · ') }}…</span>
        </button>
      </div>
    </BaseCard>

    <BaseCard>
      <template #header>템플릿 JSON 가져오기</template>
      <input type="file" accept=".json,application/json" @change="onFileImport" />
      <textarea v-model="importText" rows="4" placeholder="또는 JSON을 직접 붙여넣으세요" />
      <BaseButton variant="secondary" size="sm" :disabled="!importText.trim()" @click="onImport">가져오기</BaseButton>
    </BaseCard>

    <BaseCard>
      <template #header>현재 폴더 구조로 템플릿 만들기</template>
      <input v-model="structureName" type="text" placeholder="템플릿 이름" />
      <BaseButton variant="secondary" size="sm" :disabled="!scan.hasScanned" @click="onFromCurrentStructure">
        현재 폴더 구조로 템플릿 만들기
      </BaseButton>
    </BaseCard>

    <BaseCard>
      <template #header>폴더 목록 직접 입력</template>
      <p class="muted">원하는 폴더 구조를 한 줄에 하나씩 직접 입력해서 템플릿으로 만들 수도 있습니다.</p>
      <input v-model="folderListName" type="text" placeholder="새 템플릿 이름" />
      <textarea v-model="folderListText" rows="6" placeholder="01_경영지원&#10;02_인사&#10;영업/실적" />
      <BaseButton variant="secondary" size="sm" :disabled="!folderListText.trim()" @click="onFromFolderList">
        이 목록으로 템플릿 만들기
      </BaseButton>
    </BaseCard>

    <BaseCard v-if="template.saved.length">
      <template #header>저장된 템플릿</template>
      <ul class="template-panel__saved">
        <li v-for="t in template.saved" :key="t.name">
          <button @click="template.selectSaved(t)">{{ t.name }}</button>
        </li>
      </ul>
    </BaseCard>
  </div>
</template>

<style scoped lang="scss">
.template-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.template-panel__current {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.muted {
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
}

.template-panel__folders {
  font-family: var(--font-mono);
  font-size: 12.5px;
  background: var(--color-neutral-soft);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  margin-bottom: var(--space-4);
  white-space: pre-wrap;
}

.template-panel__actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

input[type='text'],
textarea {
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  margin: var(--space-3) 0;
  font-family: inherit;
}

textarea {
  font-family: var(--font-mono);
  font-size: 13px;
  resize: vertical;
}

.template-panel__samples-intro {
  margin-bottom: var(--space-3);
}

.template-panel__samples {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-3);
}

.template-panel__sample-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  text-align: left;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  transition: border-color var(--duration-fast) var(--ease-out), transform var(--duration-fast) var(--ease-out);

  strong {
    font-size: var(--text-sm);
  }

  &:hover {
    border-color: var(--color-accent-400);
    transform: translateY(-1px);
  }

  &--active {
    border-color: var(--color-accent-500);
    background: var(--color-accent-soft);
  }
}

.template-panel__sample-count {
  font-size: var(--text-xs);
  color: var(--color-accent-600);
}

.template-panel__sample-folders {
  font-size: 11.5px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-panel__saved {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);

  button {
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    width: 100%;
    text-align: left;

    &:hover {
      background: var(--color-accent-soft);
      color: var(--color-accent-600);
    }
  }
}
</style>
