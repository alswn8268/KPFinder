<script setup lang="ts">
import type { FileEntry } from '@/api/types'
import { SUMMARY_STATUS_LABEL } from '@/constants/status'
import BaseBadge from '@/components/base/BaseBadge.vue'
import EmptyState from '@/components/base/EmptyState.vue'

defineProps<{ entries: FileEntry[] }>()

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(1)} KB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ko-KR', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<template>
  <div v-if="entries.length === 0" class="file-table-empty">
    <EmptyState title="검색 조건에 맞는 파일이 없습니다." description="검색어 또는 필터를 변경해 주세요." icon="🔍" />
  </div>
  <div v-else class="file-table-wrap">
    <table class="file-table">
      <thead>
        <tr>
          <th>경로</th>
          <th>확장자</th>
          <th>크기</th>
          <th>수정일</th>
          <th>요약 상태</th>
        </tr>
      </thead>
      <TransitionGroup tag="tbody" name="list">
        <tr v-for="e in entries" :key="e.relative_path">
          <td class="file-table__path">{{ e.relative_path }}</td>
          <td>{{ e.ext || '(없음)' }}</td>
          <td class="num">{{ formatSize(e.size) }}</td>
          <td>{{ formatDate(e.modified) }}</td>
          <td>
            <BaseBadge v-if="e.summary_status !== 'pending'" tone="neutral" size="sm">
              {{ SUMMARY_STATUS_LABEL[e.summary_status] ?? e.summary_status }}
            </BaseBadge>
            <span v-else class="muted">대기</span>
          </td>
        </tr>
      </TransitionGroup>
    </table>
  </div>
</template>

<style scoped lang="scss">
.file-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.file-table {
  width: 100%;
  font-size: var(--text-sm);

  th {
    text-align: left;
    padding: var(--space-3) var(--space-4);
    background: var(--color-neutral-soft);
    color: var(--color-text-secondary);
    font-weight: var(--weight-semibold);
    font-size: var(--text-xs);
    position: sticky;
    top: 0;
  }

  td {
    padding: var(--space-3) var(--space-4);
    border-top: 1px solid var(--color-border);
  }

  tr:hover td {
    background: var(--color-accent-soft);
  }
}

.file-table__path {
  font-family: var(--font-mono);
  font-size: 12.5px;
}

.num {
  font-variant-numeric: tabular-nums;
}

.muted {
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
}

.file-table-empty {
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
}
</style>
