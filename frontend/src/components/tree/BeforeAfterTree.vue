<script setup lang="ts">
defineProps<{ before: string; after: string }>()
</script>

<template>
  <div class="before-after">
    <div class="before-after__col">
      <p class="before-after__label">현재 구조</p>
      <pre class="before-after__tree">{{ before }}</pre>
    </div>
    <div class="before-after__arrow" aria-hidden="true">→</div>
    <div class="before-after__col">
      <p class="before-after__label">적용 시 최종 구조(요약)</p>
      <pre class="before-after__tree before-after__tree--after">{{ after }}</pre>
    </div>
  </div>
</template>

<style scoped lang="scss">
.before-after {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: var(--space-4);
  align-items: start;
}

.before-after__label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.before-after__tree {
  font-family: var(--font-mono);
  font-size: 12.5px;
  white-space: pre-wrap;
  background: var(--color-neutral-soft);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  max-height: 360px;
  overflow: auto;
  line-height: 1.7;

  &--after {
    background: var(--color-accent-soft);
  }
}

.before-after__arrow {
  padding-top: var(--space-8);
  color: var(--color-accent-500);
  font-size: 20px;
}

@media (max-width: 800px) {
  .before-after {
    grid-template-columns: 1fr;
  }
  .before-after__arrow {
    display: none;
  }
}
</style>
