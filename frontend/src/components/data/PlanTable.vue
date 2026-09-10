<script setup lang="ts">
import type { PlanItem } from '@/api/types'

defineProps<{ plan: PlanItem[] }>()
</script>

<template>
  <div class="plan-table-wrap">
    <table>
      <thead>
        <tr>
          <th>기존 경로</th>
          <th>새 경로</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in plan" :key="p.src">
          <td class="mono">{{ p.rel_src }}</td>
          <td class="mono">{{ p.rel_dst }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped lang="scss">
.plan-table-wrap {
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
</style>
