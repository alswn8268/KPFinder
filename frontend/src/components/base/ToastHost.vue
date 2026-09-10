<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const { toasts } = storeToRefs(ui)

const ICON: Record<string, string> = {
  success: '✓',
  error: '!',
  warning: '△',
  info: 'i',
}
</script>

<template>
  <div class="toast-host">
    <TransitionGroup name="list">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="`toast--${t.type}`">
        <span class="toast__icon">{{ ICON[t.type] }}</span>
        <span class="toast__message">{{ t.message }}</span>
        <button class="toast__close" aria-label="닫기" @click="ui.dismissToast(t.id)">×</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped lang="scss">
.toast-host {
  position: fixed;
  top: var(--space-5);
  right: var(--space-5);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  width: min(360px, calc(100vw - 40px));
}

.toast {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  font-size: var(--text-sm);
}

.toast__icon {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-weight: var(--weight-bold);
  flex-shrink: 0;
}

.toast--success .toast__icon {
  background: var(--color-success-soft);
  color: var(--color-success);
}
.toast--error .toast__icon {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}
.toast--warning .toast__icon {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}
.toast--info .toast__icon {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.toast__message {
  flex: 1;
  color: var(--color-text-primary);
}

.toast__close {
  color: var(--color-text-tertiary);
  font-size: 16px;
  line-height: 1;
  &:hover {
    color: var(--color-text-primary);
  }
}
</style>
