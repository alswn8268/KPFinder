<script setup lang="ts">
withDefaults(defineProps<{ lines?: number; message?: string }>(), { lines: 3, message: '' })
</script>

<template>
  <div class="skeleton" role="status" aria-live="polite">
    <p v-if="message" class="skeleton__message">{{ message }}</p>
    <div v-for="i in lines" :key="i" class="skeleton__bar" :style="{ width: i === lines ? '60%' : '100%' }" />
  </div>
</template>

<style scoped lang="scss">
.skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-6) 0;
}

.skeleton__message {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-1);
}

.skeleton__bar {
  height: 14px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--color-neutral-soft) 25%,
    var(--color-border) 37%,
    var(--color-neutral-soft) 63%
  );
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}
</style>
