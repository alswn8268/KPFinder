<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    disabled?: boolean
    loading?: boolean
    block?: boolean
  }>(),
  {
    variant: 'primary',
    size: 'md',
    disabled: false,
    loading: false,
    block: false,
  },
)
</script>

<template>
  <button
    class="base-btn"
    :class="[`base-btn--${variant}`, `base-btn--${size}`, { 'base-btn--block': block, 'is-loading': loading }]"
    :disabled="disabled || loading"
  >
    <span v-if="loading" class="base-btn__spinner" aria-hidden="true" />
    <span class="base-btn__content"><slot /></span>
  </button>
</template>

<style scoped lang="scss">
.base-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-weight: var(--weight-semibold);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
  white-space: nowrap;

  &:active:not(:disabled) {
    transform: scale(0.97);
  }

  &:focus-visible {
    outline: none;
    box-shadow: var(--shadow-accent-glow);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.55;
  }

  &--block {
    width: 100%;
  }

  &--sm {
    padding: var(--space-2) var(--space-3);
    font-size: var(--text-sm);
  }
  &--md {
    padding: var(--space-3) var(--space-5);
    font-size: var(--text-base);
  }
  &--lg {
    padding: var(--space-4) var(--space-6);
    font-size: var(--text-md);
  }

  &--primary {
    background: var(--color-accent-500);
    color: var(--color-accent-contrast);
    box-shadow: var(--shadow-sm);
    &:hover:not(:disabled) {
      background: var(--color-accent-600);
      box-shadow: var(--shadow-md);
    }
  }

  &--secondary {
    background: var(--color-surface);
    color: var(--color-text-primary);
    border-color: var(--color-border-strong);
    &:hover:not(:disabled) {
      border-color: var(--color-accent-400);
      color: var(--color-accent-600);
    }
  }

  &--ghost {
    background: transparent;
    color: var(--color-text-secondary);
    &:hover:not(:disabled) {
      background: var(--color-neutral-soft);
      color: var(--color-text-primary);
    }
  }

  &--danger {
    background: var(--color-danger-soft);
    color: var(--color-danger);
    &:hover:not(:disabled) {
      background: var(--color-danger);
      color: #fff;
    }
  }
}

.base-btn__spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-top-color: transparent;
  opacity: 0.85;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
