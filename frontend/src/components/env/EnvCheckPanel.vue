<script setup lang="ts">
import { onMounted } from 'vue'

import BaseButton from '@/components/base/BaseButton.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import { ENV_STATUS_TONE } from '@/constants/status'
import { useClassificationStore } from '@/stores/classification'
import { useEnvStore } from '@/stores/env'
import { useScanStore } from '@/stores/scan'

const env = useEnvStore()
const scan = useScanStore()
const classification = useClassificationStore()

onMounted(() => {
  if (!env.checked) env.check(scan.root, classification.model)
})
</script>

<template>
  <div class="env-panel">
    <div class="env-panel__header">
      <p class="env-panel__hint">문제가 있는 항목만 조치하면 됩니다. AI 관련 항목이 오류여도 규칙 기반 기능은 그대로 씁니다.</p>
      <BaseButton
        variant="secondary"
        size="sm"
        :loading="env.checking"
        @click="env.check(scan.root, classification.model)"
      >
        다시 확인
      </BaseButton>
    </div>
    <TransitionGroup tag="ul" name="list" class="env-panel__list">
      <li v-for="item in env.items" :key="item.item" class="env-panel__item">
        <BaseBadge :tone="ENV_STATUS_TONE[item.status] ?? 'neutral'" size="sm">{{ item.status }}</BaseBadge>
        <div>
          <p class="env-panel__item-title">{{ item.item }}</p>
          <p class="env-panel__item-detail">{{ item.detail }}</p>
          <p v-if="item.action" class="env-panel__item-action">{{ item.action }}</p>
        </div>
      </li>
    </TransitionGroup>
  </div>
</template>

<style scoped lang="scss">
.env-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.env-panel__hint {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.env-panel__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.env-panel__item {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-neutral-soft);
}

.env-panel__item-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
}

.env-panel__item-detail {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.env-panel__item-action {
  font-size: var(--text-xs);
  color: var(--color-accent-600);
  margin-top: 2px;
}
</style>
