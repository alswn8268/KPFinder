<script setup lang="ts">
withDefaults(
  defineProps<{
    padding?: 'sm' | 'md' | 'lg'
    hoverable?: boolean
  }>(),
  { padding: 'md', hoverable: false },
)
</script>

<template>
  <section class="base-card" :class="[`base-card--${padding}`, { 'base-card--hoverable': hoverable }]">
    <header v-if="$slots.header" class="base-card__header">
      <slot name="header" />
    </header>
    <div class="base-card__body">
      <slot />
    </div>
    <footer v-if="$slots.footer" class="base-card__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<style scoped lang="scss">
.base-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  transition:
    box-shadow var(--duration-base) var(--ease-out),
    transform var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out);

  &--hoverable:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--color-accent-200);
  }

  &--sm .base-card__body {
    padding: var(--space-4);
  }
  &--md .base-card__body {
    padding: var(--space-6);
  }
  &--lg .base-card__body {
    padding: var(--space-8);
  }
}

.base-card__header {
  padding: var(--space-5) var(--space-6) 0;
  font-weight: var(--weight-semibold);
  font-size: var(--text-lg);
}

.base-card__footer {
  padding: 0 var(--space-6) var(--space-5);
}
</style>
