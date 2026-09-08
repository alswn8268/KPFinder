<script setup lang="ts">
import { ref } from 'vue'

import type { VersionInfo } from '@/api/types'
import BaseBadge from '@/components/base/BaseBadge.vue'
import BaseButton from '@/components/base/BaseButton.vue'

const props = defineProps<{ version: VersionInfo; restoring: boolean }>()
const emit = defineEmits<{ restore: [string] }>()

const open = ref(false)

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString('ko-KR')
}
</script>

<template>
  <div class="version-card">
    <button class="version-card__header" @click="open = !open">
      <span class="version-card__chevron" :class="{ 'is-open': open }">›</span>
      <span class="version-card__id">{{ version.version_id }}</span>
      <span class="version-card__meta">{{ formatTimestamp(version.timestamp) }} · {{ version.files_moved }}개 파일 이동</span>
      <BaseBadge :tone="version.restored ? 'neutral' : 'success'" size="sm">
        {{ version.restored ? '↩️ 되돌려짐' : '✅ 적용됨' }}
      </BaseBadge>
    </button>
    <Transition name="rise">
      <div v-if="open" class="version-card__body">
        <p v-if="version.note">{{ version.note }}</p>
        <template v-if="!version.restored">
          <BaseButton
            variant="danger"
            size="sm"
            :disabled="!version.can_restore"
            :loading="restoring"
            @click="emit('restore', version.version_id)"
          >
            이 버전 되돌리기
          </BaseButton>
          <p v-if="!version.can_restore" class="version-card__blocked">{{ version.restore_blocked_reason }}</p>
        </template>
        <p v-else class="version-card__blocked">이미 되돌려진 버전입니다.</p>
      </div>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
.version-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.version-card__header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  font-size: var(--text-sm);
  text-align: left;

  &:hover {
    background: var(--color-neutral-soft);
  }
}

.version-card__chevron {
  color: var(--color-text-tertiary);
  transition: transform var(--duration-base) var(--ease-out);
  &.is-open {
    transform: rotate(90deg);
  }
}

.version-card__id {
  font-weight: var(--weight-bold);
  color: var(--color-accent-600);
}

.version-card__meta {
  flex: 1;
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
}

.version-card__body {
  padding: 0 var(--space-4) var(--space-4) var(--space-9);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-items: flex-start;
}

.version-card__blocked {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}
</style>
