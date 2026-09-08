<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useApplyStore } from '@/stores/apply'
import { useClassificationStore } from '@/stores/classification'
import { useScanStore } from '@/stores/scan'

const route = useRoute()
const scan = useScanStore()
const classification = useClassificationStore()
const applyStore = useApplyStore()

const steps = computed(() => [
  { key: 'scan', label: '스캔', routes: ['scan'], done: scan.hasScanned },
  { key: 'classify', label: '분류', routes: ['classify'], done: classification.hasResult },
  { key: 'proposal', label: '편집', routes: ['proposal'], done: classification.hasResult },
  { key: 'apply', label: '적용', routes: ['apply'], done: !!applyStore.lastResult },
])

const currentIndex = computed(() => steps.value.findIndex((s) => s.routes.includes(route.name as string)))
</script>

<template>
  <ol class="steps" aria-label="진행 단계">
    <li
      v-for="(step, i) in steps"
      :key="step.key"
      class="steps__item"
      :class="{
        'is-current': i === currentIndex,
        'is-done': step.done && i !== currentIndex,
      }"
    >
      <span class="steps__dot">
        <Transition name="fade" mode="out-in">
          <span v-if="step.done && i !== currentIndex" key="check">✓</span>
          <span v-else key="num">{{ i + 1 }}</span>
        </Transition>
      </span>
      <span class="steps__label">{{ step.label }}</span>
    </li>
  </ol>
</template>

<style scoped lang="scss">
.steps {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.steps__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);

  &:not(:last-child)::after {
    content: '';
    width: 24px;
    height: 1px;
    background: var(--color-border-strong);
    margin-left: var(--space-2);
  }
}

.steps__dot {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1.5px solid var(--color-border-strong);
  font-size: 11px;
  transition: all var(--duration-base) var(--ease-out);
}

.is-current {
  color: var(--color-accent-600);
  .steps__dot {
    background: var(--color-accent-500);
    border-color: var(--color-accent-500);
    color: #fff;
    box-shadow: var(--shadow-accent-glow);
  }
}

.is-done {
  color: var(--color-text-secondary);
  .steps__dot {
    background: var(--color-success-soft);
    border-color: var(--color-success);
    color: var(--color-success);
  }
}
</style>
