<script setup lang="ts">
// 실행 환경 점검은 AppShell이 (모델이 바뀔 때마다 다시) 트리거한다 — 여기서는 순수하게
// "문제가 있는지 없는지"만 작은 표시등으로 보여준다. 자세한 목록은 클릭해서 여는
// EnvDetailModal 쪽 책임이다.
import { computed } from 'vue'

import { useEnvStore } from '@/stores/env'

const env = useEnvStore()

const hasIssue = computed(() => env.items.some((i) => i.status !== '정상'))
</script>

<template>
  <span class="env-strip" :class="{ 'is-loading': env.checking, 'is-issue': hasIssue }">
    <span class="env-strip__dot" />
    실행 환경
  </span>
</template>

<style scoped lang="scss">
.env-strip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  transition: opacity var(--duration-fast) var(--ease-out);

  &.is-loading {
    opacity: 0.6;
  }
}

.env-strip__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-success);
  flex-shrink: 0;
  animation: env-dot-pulse 2.2s var(--ease-in-out) infinite;
}

.env-strip.is-issue .env-strip__dot {
  background: var(--color-warning);
  animation-name: env-dot-pulse-warn;
}

@keyframes env-dot-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 var(--color-success-soft);
  }
  50% {
    box-shadow: 0 0 0 4px transparent;
  }
}

@keyframes env-dot-pulse-warn {
  0%,
  100% {
    box-shadow: 0 0 0 0 var(--color-warning-soft);
  }
  50% {
    box-shadow: 0 0 0 4px transparent;
  }
}
</style>
