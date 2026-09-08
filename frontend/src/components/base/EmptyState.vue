<script setup lang="ts">
withDefaults(defineProps<{ title: string; description?: string; icon?: string }>(), {
  description: '',
  icon: '📄',
})
</script>

<template>
  <div class="empty-state">
    <div class="empty-state__icon" aria-hidden="true">{{ icon }}</div>
    <p class="empty-state__title">{{ title }}</p>
    <p v-if="description" class="empty-state__desc">{{ description }}</p>
    <div v-if="$slots.action" class="empty-state__action">
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-12) var(--space-6);
  color: var(--color-text-secondary);
}

.empty-state__icon {
  font-size: 40px;
  margin-bottom: var(--space-3);
  opacity: 0.8;
}

.empty-state__title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text-primary);
}

.empty-state__desc {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  max-width: 40ch;
}

.empty-state__action {
  margin-top: var(--space-4);
}
</style>
