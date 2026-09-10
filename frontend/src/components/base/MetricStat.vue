<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    value: string | number
    tone?: 'accent' | 'success' | 'warning' | 'danger' | 'neutral'
  }>(),
  { tone: 'neutral' },
)
</script>

<template>
  <div class="metric" :class="`metric--${tone}`">
    <span class="metric__value">{{ value }}</span>
    <span class="metric__label">{{ label }}</span>
  </div>
</template>

<style scoped lang="scss">
.metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  min-width: 96px;
  transition: transform var(--duration-base) var(--ease-out);
  animation: rise-in var(--duration-slow) var(--ease-out);

  &:hover {
    transform: translateY(-2px);
  }
}

.metric__value {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  font-variant-numeric: tabular-nums;
}

.metric__label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.metric--accent .metric__value {
  color: var(--color-accent-600);
}
.metric--success .metric__value {
  color: var(--color-success);
}
.metric--warning .metric__value {
  color: var(--color-warning);
}
.metric--danger .metric__value {
  color: var(--color-danger);
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
