<script setup lang="ts">
import type { VersionInfo } from '@/api/types'
import BaseBadge from '@/components/base/BaseBadge.vue'
import BaseButton from '@/components/base/BaseButton.vue'

const props = defineProps<{ version: VersionInfo; restoring: boolean }>()
const emit = defineEmits<{ restore: [string] }>()

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString('ko-KR')
}
</script>

<template>
  <div class="version-card">
    <div class="version-card__row">
      <span class="version-card__id">{{ version.version_id }}</span>
      <span class="version-card__meta">{{ formatTimestamp(version.timestamp) }} · {{ version.files_moved }}개 파일 이동</span>
      <BaseBadge :tone="version.restored ? 'neutral' : 'success'" size="sm">
        {{ version.restored ? '↩️ 되돌려짐' : '✅ 적용됨' }}
      </BaseBadge>
      <BaseButton
        v-if="!version.restored"
        variant="danger"
        size="sm"
        :disabled="!version.can_restore"
        :loading="restoring"
        @click="emit('restore', version.version_id)"
      >
        이 버전 되돌리기
      </BaseButton>
    </div>
    <p v-if="version.note" class="version-card__note">{{ version.note }}</p>
    <p v-if="!version.restored && !version.can_restore" class="version-card__blocked">
      {{ version.restore_blocked_reason }}
    </p>
  </div>
</template>

<style scoped lang="scss">
.version-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.version-card__row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.version-card__id {
  font-weight: var(--weight-bold);
  color: var(--color-accent-600);
  font-size: var(--text-sm);
}

.version-card__meta {
  flex: 1;
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
}

.version-card__note {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.version-card__blocked {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}
</style>
