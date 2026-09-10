<script setup lang="ts">
import type { BadgeTone } from '@/constants/status'

withDefaults(defineProps<{ tone?: BadgeTone; size?: 'sm' | 'md' }>(), {
  tone: 'neutral',
  size: 'md',
})
</script>

<template>
  <span class="badge" :class="[`badge--${tone}`, `badge--${size}`]"><slot /></span>
</template>

<style scoped lang="scss">
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: var(--radius-full);
  font-weight: var(--weight-medium);
  white-space: nowrap;

  &--sm {
    padding: 2px 8px;
    font-size: 11px;
  }
  &--md {
    padding: 4px 10px;
    font-size: var(--text-xs);
  }

  &--success {
    background: var(--color-success-soft);
    color: var(--color-success);
  }
  &--warning {
    background: var(--color-warning-soft);
    color: var(--color-warning);
  }
  &--danger {
    background: var(--color-danger-soft);
    color: var(--color-danger);
  }
  &--info {
    background: var(--color-info-soft);
    color: var(--color-info);
  }
  &--neutral {
    background: var(--color-neutral-soft);
    color: var(--color-neutral);
  }
  &--accent {
    background: var(--color-accent-soft);
    color: var(--color-accent-600);
  }
}
</style>
