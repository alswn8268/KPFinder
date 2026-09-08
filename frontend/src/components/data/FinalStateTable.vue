<script setup lang="ts">
import { computed } from 'vue'

import BaseBadge from '@/components/base/BaseBadge.vue'
import { FINAL_STATE_TONE } from '@/constants/status'

const props = defineProps<{ rows: Record<string, string>[] }>()

const statusCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const row of props.rows) {
    counts.set(row['상태'], (counts.get(row['상태']) ?? 0) + 1)
  }
  return Array.from(counts.entries())
})
</script>

<template>
  <div class="final-state">
    <div class="final-state__summary">
      <BaseBadge v-for="[status, count] in statusCounts" :key="status" :tone="FINAL_STATE_TONE[status] ?? 'neutral'">
        {{ status }} {{ count }}개
      </BaseBadge>
    </div>
    <div class="final-state-wrap">
      <table>
        <thead>
          <tr>
            <th>경로</th>
            <th>상태</th>
            <th>목적지</th>
            <th>비고</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in rows" :key="i">
            <td class="mono">{{ row['경로'] }}</td>
            <td><BaseBadge :tone="FINAL_STATE_TONE[row['상태']] ?? 'neutral'" size="sm">{{ row['상태'] }}</BaseBadge></td>
            <td class="mono">{{ row['목적지'] }}</td>
            <td class="muted">{{ row['비고'] }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped lang="scss">
.final-state__summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.final-state-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  max-height: 420px;
  overflow-y: auto;
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
    position: sticky;
    top: 0;
  }

  td {
    padding: var(--space-2) var(--space-3);
    border-top: 1px solid var(--color-border);
  }
}

.mono {
  font-family: var(--font-mono);
  font-size: 12.5px;
}

.muted {
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
}
</style>
