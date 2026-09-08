<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { buildRenameAssignments, previewRename } from '@/api/rename'
import { applyPlan } from '@/api/apply'
import type { RenameMode, RenamePreviewRow } from '@/api/types'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import { useScanStore } from '@/stores/scan'
import { useUiStore } from '@/stores/ui'

const scan = useScanStore()
const ui = useUiStore()

const extFilter = ref('')
const queryFilter = ref('')
const mode = ref<RenameMode>('find_replace')
const find = ref('')
const replace = ref('')
const text = ref('')
const baseName = ref('')
const start = ref(1)
const digits = ref(3)
const rows = ref<RenamePreviewRow[]>([])
const confirmChecked = ref(false)
const applying = ref(false)

const allExts = computed(() => Array.from(new Set(scan.entries.map((e) => e.ext || '(없음)'))).sort())

const targetEntries = computed(() => {
  let items = scan.entries
  if (extFilter.value) items = items.filter((e) => (e.ext || '(없음)') === extFilter.value)
  if (queryFilter.value.trim()) {
    const q = queryFilter.value.trim().toLowerCase()
    items = items.filter((e) => e.relative_path.toLowerCase().includes(q))
  }
  return items
})

const rule = computed(() => ({
  mode: mode.value,
  find: find.value,
  replace: replace.value,
  text: text.value,
  base_name: baseName.value,
  start: start.value,
  digits: digits.value,
}))

const changedRows = computed(() => rows.value.filter((r) => r.changed))

async function refreshPreview() {
  if (targetEntries.value.length === 0) {
    rows.value = []
    return
  }
  rows.value = await previewRename(targetEntries.value, rule.value)
}

watch([targetEntries, rule], refreshPreview, { immediate: true, deep: true })

async function onApply() {
  applying.value = true
  try {
    const assignments = await buildRenameAssignments(targetEntries.value, rule.value)
    const result = await applyPlan(scan.root, assignments, scan.entries, '파일명 일괄 변경')
    ui.pushToast(`${result.moved_count}개 파일의 이름을 변경했습니다.`, 'success')
    await scan.scan(scan.root)
    confirmChecked.value = false
  } finally {
    applying.value = false
  }
}
</script>

<template>
  <div class="rename-view">
    <p class="rename-view__intro">
      선택한 파일들의 이름을 규칙에 따라 한 번에 바꿉니다. 실제로는 '같은 폴더로 이름만 바꿔
      이동'하는 것과 같아서, 이동 계획과 똑같은 안전성 검사(경로 보호, 덮어쓰기 금지, 실패 시
      자동 복구)와 되돌리기가 그대로 적용됩니다.
    </p>

    <BaseCard>
      <div class="rename-view__filters">
        <select v-model="extFilter">
          <option value="">대상 확장자(전체)</option>
          <option v-for="ext in allExts" :key="ext" :value="ext">{{ ext }}</option>
        </select>
        <input v-model="queryFilter" type="text" placeholder="파일명/경로 검색" />
      </div>
      <p class="rename-view__count">대상 파일 {{ targetEntries.length }}개</p>

      <div class="rename-view__mode">
        <label v-for="m in (['find_replace', 'prefix', 'suffix', 'numbering'] as RenameMode[])" :key="m">
          <input v-model="mode" type="radio" :value="m" />
          {{ { find_replace: '찾기/바꾸기', prefix: '앞에 문구 추가', suffix: '뒤에 문구 추가', numbering: '일련번호로 통일' }[m] }}
        </label>
      </div>

      <div v-if="mode === 'find_replace'" class="rename-view__inputs">
        <input v-model="find" type="text" placeholder="찾을 문자열" />
        <input v-model="replace" type="text" placeholder="바꿀 문자열" />
      </div>
      <div v-else-if="mode === 'prefix' || mode === 'suffix'" class="rename-view__inputs">
        <input v-model="text" type="text" placeholder="추가할 문구" />
      </div>
      <div v-else class="rename-view__inputs rename-view__inputs--three">
        <input v-model="baseName" type="text" placeholder="기본 이름(비워두면 원래 이름 유지)" />
        <input v-model.number="start" type="number" min="0" placeholder="시작 번호" />
        <input v-model.number="digits" type="number" min="1" max="6" placeholder="자릿수" />
      </div>

      <table v-if="rows.length" class="rename-view__table">
        <thead>
          <tr>
            <th>기존 이름</th>
            <th>새 이름</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.src" :class="{ 'is-changed': r.changed }">
            <td>{{ r.old_name }}</td>
            <td>{{ r.new_name }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="changedRows.length" class="rename-view__apply">
        <p class="rename-view__warning">{{ changedRows.length }}개 파일의 이름이 바뀝니다. 적용 전 위 내용을 확인하세요.</p>
        <label class="rename-view__confirm">
          <input v-model="confirmChecked" type="checkbox" />
          위 이름 변경 계획을 확인했으며, 실제로 적용하는 데 동의합니다.
        </label>
        <BaseButton :disabled="!confirmChecked" :loading="applying" @click="onApply">✂️ 이름 일괄 변경 적용</BaseButton>
      </div>
    </BaseCard>
  </div>
</template>

<style scoped lang="scss">
.rename-view__intro {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  max-width: 90ch;
  margin-bottom: var(--space-6);
}

.rename-view__filters {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-3);

  select,
  input {
    padding: var(--space-3);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
  }
  input {
    flex: 1;
  }
}

.rename-view__count {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-4);
}

.rename-view__mode {
  display: flex;
  gap: var(--space-5);
  margin-bottom: var(--space-4);
  font-size: var(--text-sm);

  label {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  input {
    accent-color: var(--color-accent-500);
  }
}

.rename-view__inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  margin-bottom: var(--space-5);

  &--three {
    grid-template-columns: 2fr 1fr 1fr;
  }

  input {
    padding: var(--space-3);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
  }
}

.rename-view__table {
  width: 100%;
  font-size: var(--text-sm);
  margin-bottom: var(--space-5);

  th {
    text-align: left;
    padding: var(--space-2) var(--space-3);
    color: var(--color-text-secondary);
    font-size: var(--text-xs);
  }

  td {
    padding: var(--space-2) var(--space-3);
    border-top: 1px solid var(--color-border);
  }

  tr.is-changed td:last-child {
    color: var(--color-accent-600);
    font-weight: var(--weight-medium);
  }
}

.rename-view__warning {
  font-size: var(--text-sm);
  color: var(--color-warning);
  margin-bottom: var(--space-3);
}

.rename-view__confirm {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  margin-bottom: var(--space-4);

  input {
    accent-color: var(--color-accent-500);
  }
}
</style>
