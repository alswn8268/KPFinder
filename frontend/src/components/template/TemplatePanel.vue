<script setup lang="ts">
import { computed, ref } from 'vue'

import { exportTemplate } from '@/api/templates'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import { downloadBlob } from '@/utils/download'
import { useClassificationStore } from '@/stores/classification'
import { useScanStore } from '@/stores/scan'
import { useTemplateStore } from '@/stores/template'
import { useUiStore } from '@/stores/ui'

const template = useTemplateStore()
const scan = useScanStore()
const classification = useClassificationStore()
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

const EXAMPLE_FOLDER_LIST = `# '#'으로 시작하는 줄은 주석이라 무시됩니다
01_기획·전략
02_인사·총무
03_재무·회계
04_계약·법무
# '/'로 하위 폴더도 만들 수 있어요
05_영업/국내
05_영업/해외
06_마케팅·홍보
07_회의록`

function onFillExample() {
  folderListText.value = EXAMPLE_FOLDER_LIST
  folderListName.value = folderListName.value.trim() || '내 템플릿'
}

async function onSave() {
  await template.persist()
  ui.pushToast('템플릿을 저장했습니다.', 'success')
}

const structureHint = ref('')
const structureMode = ref<'free' | 'hybrid'>('free')
const aiTemplateName = ref('AI 제안 템플릿')

const suggestionRows = computed(() =>
  template.suggestion
    ? Object.entries(template.suggestion.assignments).map(([src, info]) => ({ src, ...info }))
    : [],
)

function ensureReadyToSuggest(): boolean {
  if (!scan.hasScanned) {
    ui.pushToast('먼저 폴더를 스캔하세요.', 'warning')
    return false
  }
  const summarizedCount = scan.entries.filter(
    (e) => e.summary_status === 'ok' || e.summary_status === 'empty',
  ).length
  if (summarizedCount === 0) {
    ui.pushToast(
      '아직 요약된 파일이 없습니다. 먼저 분류를 한 번 실행해 파일 요약을 만든 뒤 다시 시도하세요.',
      'warning',
    )
    return false
  }
  return true
}

async function onSuggestStructure() {
  if (!ensureReadyToSuggest()) return
  if (!classification.model) await classification.loadDefaultModel()
  try {
    if (structureMode.value === 'hybrid') {
      if (!template.active) {
        ui.pushToast('기준으로 삼을 현재 템플릿이 없습니다.', 'warning')
        return
      }
      await template.suggestHybridStructure(scan.entries, template.active, classification.model, structureHint.value)
    } else {
      await template.suggestNewStructure(scan.entries, classification.model, structureHint.value)
    }
  } catch {
    ui.pushToast('AI 제안을 받아오지 못했습니다.', 'error')
  }
}

async function onRetrySuggestion(adjustment = '') {
  if (!ensureReadyToSuggest()) return
  try {
    await template.retrySuggestion(scan.entries, classification.model, adjustment)
  } catch {
    ui.pushToast('AI 제안을 다시 받아오지 못했습니다.', 'error')
  }
}

async function onSaveAiProposal() {
  try {
    const saved = await template.fromAiProposal(aiTemplateName.value.trim() || 'AI 제안 템플릿')
    ui.pushToast(`템플릿 '${saved?.name}'을(를) 만들었습니다.`, 'success')
  } catch {
    ui.pushToast('템플릿을 만들지 못했습니다.', 'error')
  }
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

      <div class="template-panel__howto">
        <p class="template-panel__howto-title">✏️ 작성 방법</p>
        <ul>
          <li>한 줄에 폴더 경로 하나씩 적습니다.</li>
          <li>하위 폴더는 <code>상위/하위</code> 형식으로 씁니다(예: <code>영업/국내</code>).</li>
          <li><code>#</code>으로 시작하는 줄은 주석으로 무시됩니다. 빈 줄도 무시됩니다.</li>
          <li>분류되지 않는 파일을 담을 <code>99_미분류</code> 폴더는 없으면 자동으로 추가됩니다.</li>
          <li>이렇게 만든 템플릿은 키워드 규칙이 비어 있어 처음엔 AI 분류에만 쓰입니다 — 아래
            "저장"으로 남겨두고 필요하면 JSON을 내보내 규칙을 직접 추가할 수 있습니다.</li>
        </ul>
        <button type="button" class="template-panel__example-btn" @click="onFillExample">
          예시로 채워보기
        </button>
      </div>

      <input v-model="folderListName" type="text" placeholder="새 템플릿 이름" />
      <textarea v-model="folderListText" rows="6" placeholder="01_경영지원&#10;02_인사&#10;영업/실적" />
      <BaseButton variant="secondary" size="sm" :disabled="!folderListText.trim()" @click="onFromFolderList">
        이 목록으로 템플릿 만들기
      </BaseButton>
    </BaseCard>

    <BaseCard>
      <template #header>🤖 AI에게 새 구조 제안받기</template>
      <p class="muted">
        지금 스캔된 파일 내용을 보고 AI가 새로운 구조를 제안합니다. 파일이 많으면 서버가
        자동으로 나눠서 요청합니다. 제안은 바로 템플릿이 되지 않으며, 아래에서 검토한 뒤
        저장해야 적용됩니다.
      </p>
      <div class="template-panel__mode-toggle">
        <label>
          <input v-model="structureMode" type="radio" value="free" />
          완전 새 구조
        </label>
        <label>
          <input v-model="structureMode" type="radio" value="hybrid" />
          하이브리드(현재 템플릿 유지 + 부족한 것만 추가)
        </label>
      </div>
      <input v-model="structureHint" type="text" placeholder="요청사항(선택) 예: 부서별로 나눠줘, 연도별로 나눠줘" />
      <BaseButton
        variant="secondary"
        size="sm"
        :disabled="!scan.hasScanned"
        :loading="template.suggesting"
        @click="onSuggestStructure"
      >
        AI에게 구조 제안받기
      </BaseButton>

      <template v-if="template.suggestion">
        <p v-if="template.suggestionMode === 'hybrid'" class="muted template-panel__suggestion-notes">
          하이브리드 모드: 현재 템플릿 폴더는 유지되고, 부족한 카테고리만 추가됩니다.
        </p>
        <p v-if="template.suggestion.notes" class="muted template-panel__suggestion-notes">
          💬 {{ template.suggestion.notes }}
        </p>
        <p v-if="template.suggestion.categories.length" class="template-panel__suggestion-categories">
          <strong>제안된 카테고리:</strong> {{ template.suggestion.categories.join(', ') }}
        </p>
        <div v-if="suggestionRows.length" class="template-panel__suggestion-table-wrap">
          <table class="template-panel__suggestion-table">
            <thead>
              <tr>
                <th>파일</th>
                <th>제안 위치</th>
                <th>이유</th>
                <th>신뢰도</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in suggestionRows" :key="row.src">
                <td>{{ row.src }}</td>
                <td>{{ row.dst }}</td>
                <td>{{ row.reason }}</td>
                <td>{{ row.confidence }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="muted">마음에 안 들면 힌트를 바꾸지 않고도 바로 다시 받을 수 있습니다.</p>
        <div class="template-panel__retry-row">
          <BaseButton variant="ghost" size="sm" :loading="template.suggesting" @click="onRetrySuggestion()">
            🔁 그대로 다시
          </BaseButton>
          <BaseButton variant="ghost" size="sm" :loading="template.suggesting" @click="onRetrySuggestion('fewer')">
            ➖ 카테고리 더 적게
          </BaseButton>
          <BaseButton variant="ghost" size="sm" :loading="template.suggesting" @click="onRetrySuggestion('more')">
            ➕ 카테고리 더 많게
          </BaseButton>
        </div>

        <input v-model="aiTemplateName" type="text" placeholder="이 제안으로 만들 템플릿 이름" />
        <BaseButton
          variant="secondary"
          size="sm"
          :disabled="!template.suggestion.categories.length && template.suggestionMode !== 'hybrid'"
          @click="onSaveAiProposal"
        >
          이 제안을 템플릿으로 저장
        </BaseButton>
      </template>
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

.template-panel__howto {
  background: var(--color-accent-soft);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  margin: var(--space-3) 0;
}

.template-panel__howto-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  margin-bottom: var(--space-2);
}

.template-panel__howto ul {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding-left: var(--space-5);
  margin-bottom: var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  list-style: disc;
}

.template-panel__howto code {
  font-family: var(--font-mono);
  font-size: 11.5px;
  background: var(--color-surface);
  padding: 1px 5px;
  border-radius: var(--radius-sm, 4px);
}

.template-panel__example-btn {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-accent-600);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-accent-400);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  transition: background-color var(--duration-fast) var(--ease-out);

  &:hover {
    background: var(--color-accent-100);
  }
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

.template-panel__mode-toggle {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin: var(--space-3) 0;
  font-size: var(--text-sm);

  label {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    cursor: pointer;
  }
}

.template-panel__retry-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin: var(--space-3) 0;
}

.template-panel__suggestion-notes {
  margin-top: var(--space-2);
}

.template-panel__suggestion-categories {
  font-size: var(--text-sm);
  margin: var(--space-2) 0;
}

.template-panel__suggestion-table-wrap {
  overflow-x: auto;
  margin: var(--space-3) 0;
}

.template-panel__suggestion-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);

  th,
  td {
    border: 1px solid var(--color-border-strong);
    padding: var(--space-2) var(--space-3);
    text-align: left;
    white-space: nowrap;
  }

  th {
    background: var(--color-neutral-soft);
  }
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
