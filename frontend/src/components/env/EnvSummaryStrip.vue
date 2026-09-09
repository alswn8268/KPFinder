<script setup lang="ts">
import { onMounted } from 'vue'

import { useEnvStore } from '@/stores/env'
import { useScanStore } from '@/stores/scan'

const env = useEnvStore()
const scan = useScanStore()

onMounted(() => {
  if (!env.checked) env.check(scan.root)
})

const SHORT_LABEL: Record<string, string> = {
  'Python 실행 환경': 'Python',
  '필수 라이브러리': '라이브러리',
  'Ollama 실행 여부': 'Ollama',
  'AI 모델 설치 여부': 'AI 모델',
  '캐시 저장 위치': '캐시',
  '여유 저장 공간': '저장공간',
  운영체제: 'OS',
}

const STATUS_ICON: Record<string, string> = {
  정상: '✅',
  주의: '⚠️',
  오류: '❌',
}
</script>

<template>
  <div class="env-strip" :class="{ 'is-loading': env.checking }">
    <span class="env-strip__label">🩺 실행 환경</span>
    <TransitionGroup name="chip" tag="span" class="env-strip__chips">
      <span
        v-for="(item, i) in env.items"
        :key="item.item"
        class="env-strip__chip"
        :class="`env-strip__chip--${item.status}`"
        :style="{ transitionDelay: `${i * 40}ms` }"
        :title="`${item.item}: ${item.detail}`"
      >
        {{ STATUS_ICON[item.status] ?? '•' }} {{ SHORT_LABEL[item.item] ?? item.item }}
      </span>
    </TransitionGroup>
    <span v-if="!env.items.length && env.checking" class="env-strip__loading">확인 중…</span>
  </div>
</template>

<style scoped lang="scss">
.env-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  max-width: min(420px, 46vw);
  transition: opacity var(--duration-fast) var(--ease-out);

  &.is-loading {
    opacity: 0.6;
  }
}

.env-strip__label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text-tertiary);
  margin-right: var(--space-1);
}

.env-strip__chips {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.env-strip__chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11.5px;
  font-weight: var(--weight-medium);
  padding: 3px 9px;
  border-radius: var(--radius-full, 999px);
  background: var(--color-neutral-soft);
  color: var(--color-text-secondary);
  white-space: nowrap;
  cursor: default;
  transition:
    transform var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);

  &:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-xs);
  }

  &--오류 {
    background: var(--color-danger-soft);
    color: var(--color-danger);
    animation: chip-alert-pulse 2s var(--ease-in-out) infinite;
  }

  &--주의 {
    background: var(--color-warning-soft);
    color: var(--color-warning);
    animation: chip-alert-pulse 2s var(--ease-in-out) infinite;
  }
}

@keyframes chip-alert-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, currentColor 30%, transparent);
  }
  50% {
    box-shadow: 0 0 0 4px transparent;
  }
}

.env-strip__loading {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.chip-enter-active {
  transition: opacity var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out);
}
.chip-enter-from {
  opacity: 0;
  transform: scale(0.6) translateY(4px);
}
.chip-move {
  transition: transform var(--duration-base) var(--ease-out);
}
</style>
