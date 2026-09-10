<script setup lang="ts">
import { computed, ref } from 'vue'

import BaseBadge from '@/components/base/BaseBadge.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import { CONFIDENCE_TONE, SOURCE_LABEL } from '@/constants/status'
import { useEditStore } from '@/stores/edit'
import { useTemplateStore } from '@/stores/template'

const edit = useEditStore()
const template = useTemplateStore()

const confidenceFilter = ref<string[]>([])
const sourceFilter = ref<string[]>([])
const modifiedOnly = ref(false)
const bulkTarget = ref('')

interface Row {
  src: string
  dst: string
  reason: string
  confidence: string
  source: string
  applied: boolean
}

const rows = computed<Row[]>(() =>
  Object.entries(edit.valid).map(([src, info]) => {
    const override = edit.overrides[src]
    return {
      src,
      dst: override?.dst ?? info.dst,
      reason: info.reason,
      confidence: info.confidence,
      source: info.source,
      applied: !(override?.excluded ?? false),
    }
  }),
)

const filteredRows = computed(() =>
  rows.value.filter((r) => {
    if (confidenceFilter.value.length && !confidenceFilter.value.includes(r.confidence)) return false
    if (sourceFilter.value.length && !sourceFilter.value.includes(SOURCE_LABEL[r.source] ?? r.source)) return false
    if (modifiedOnly.value && !(r.src in edit.overrides)) return false
    return true
  }),
)

async function onToggleApplied(row: Row) {
  edit.setOverride(row.src, row.dst, !row.applied)
  await edit.refresh()
}

async function onDestinationChange(row: Row, value: string) {
  edit.setOverride(row.src, value, !row.applied)
  await edit.refresh()
}

async function applyBulkTarget() {
  if (!bulkTarget.value.trim()) return
  edit.bulkSetDestination(
    filteredRows.value.map((r) => r.src),
    bulkTarget.value.trim(),
  )
  await edit.refresh()
}

async function resetFiltered() {
  edit.resetToSuggestion(filteredRows.value.map((r) => r.src))
  await edit.refresh()
}
</script>

<template>
  <div class="proposal-table">
    <p class="proposal-table__desc">
      AI/규칙이 제안한 파일별 목적지입니다. 적용 여부를 끄거나 목적지를 직접 고쳐 쓸 수 있습니다.
    </p>

    <div class="proposal-table__filters">
      <div class="proposal-table__multiselect">
        <label v-for="c in ['높음', '보통', '낮음']" :key="c">
          <input v-model="confidenceFilter" type="checkbox" :value="c" />
          {{ c }}
        </label>
      </div>
      <label class="proposal-table__checkbox">
        <input v-model="modifiedOnly" type="checkbox" />
        수정된 항목만 보기
      </label>
    </div>

    <div class="proposal-table-wrap">
      <table>
        <thead>
          <tr>
            <th>적용</th>
            <th>경로</th>
            <th>신뢰도</th>
            <th>추천 이유</th>
            <th>출처</th>
            <th>최종 폴더</th>
          </tr>
        </thead>
        <TransitionGroup tag="tbody" name="list">
          <tr v-for="row in filteredRows" :key="row.src" :class="{ 'is-excluded': !row.applied }">
            <td>
              <input type="checkbox" :checked="row.applied" @change="onToggleApplied(row)" />
            </td>
            <td class="mono">{{ row.src }}</td>
            <td><BaseBadge :tone="CONFIDENCE_TONE[row.confidence] ?? 'neutral'" size="sm">{{ row.confidence }}</BaseBadge></td>
            <td class="proposal-table__reason">{{ row.reason }}</td>
            <td>{{ SOURCE_LABEL[row.source] ?? row.source }}</td>
            <td>
              <input
                class="proposal-table__dst-input"
                :value="row.dst"
                :list="`folder-options`"
                :disabled="!row.applied"
                @change="onDestinationChange(row, ($event.target as HTMLInputElement).value)"
              />
            </td>
          </tr>
        </TransitionGroup>
      </table>
      <datalist id="folder-options">
        <option v-for="f in template.active?.folders ?? []" :key="f.path" :value="f.path + '/'" />
      </datalist>
    </div>

    <details class="proposal-table__bulk">
      <summary>일괄 수정</summary>
      <div class="proposal-table__bulk-row">
        <input v-model="bulkTarget" type="text" placeholder="현재 필터에 표시된 모든 항목의 새 목적지 폴더" />
        <BaseButton variant="secondary" size="sm" :disabled="!bulkTarget.trim()" @click="applyBulkTarget">
          일괄 폴더 변경 적용
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="resetFiltered">표시된 항목을 AI/규칙 제안으로 되돌리기</BaseButton>
      </div>
    </details>

    <details v-if="edit.history.length" class="proposal-table__bulk">
      <summary>✏️ 수정 내역 ({{ edit.history.length }}건)</summary>
      <table class="proposal-table__history">
        <thead>
          <tr>
            <th>경로</th>
            <th>AI/규칙 제안</th>
            <th>사용자 최종</th>
            <th>수정 시각</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(h, i) in edit.history" :key="i">
            <td class="mono">{{ h.src }}</td>
            <td>{{ h.aiDst }}</td>
            <td>{{ h.userDst }}</td>
            <td>{{ h.at }}</td>
          </tr>
        </tbody>
      </table>
    </details>
  </div>
</template>

<style scoped lang="scss">
.proposal-table__desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-4);
}

.proposal-table__filters {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  margin-bottom: var(--space-4);
  font-size: var(--text-sm);
}

.proposal-table__multiselect {
  display: flex;
  gap: var(--space-4);

  label {
    display: flex;
    align-items: center;
    gap: var(--space-1);
  }
}

.proposal-table__checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.proposal-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

table {
  width: 100%;
  font-size: var(--text-sm);

  th {
    text-align: left;
    padding: var(--space-3);
    background: var(--color-neutral-soft);
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
  }

  td {
    padding: var(--space-2) var(--space-3);
    border-top: 1px solid var(--color-border);
    vertical-align: middle;
  }

  tr.is-excluded {
    opacity: 0.5;
  }
}

.mono {
  font-family: var(--font-mono);
  font-size: 12.5px;
}

.proposal-table__reason {
  max-width: 240px;
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
}

.proposal-table__dst-input {
  width: 100%;
  min-width: 220px;
  padding: var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 12.5px;

  &:focus {
    outline: none;
    border-color: var(--color-accent-500);
  }
}

.proposal-table__bulk {
  margin-top: var(--space-4);
  font-size: var(--text-sm);

  summary {
    cursor: pointer;
    font-weight: var(--weight-medium);
    color: var(--color-accent-600);
  }
}

.proposal-table__bulk-row {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-3);
  align-items: center;

  input {
    flex: 1;
    padding: var(--space-2) var(--space-3);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
  }
}

.proposal-table__history {
  margin-top: var(--space-3);
  width: 100%;
  font-size: var(--text-xs);

  th,
  td {
    padding: var(--space-2);
    border-top: 1px solid var(--color-border);
    text-align: left;
  }
}
</style>
