<script setup lang="ts">
const minScore = defineModel<number>('minScore', { default: 0.35 })
const showLabels = defineModel<boolean>('showLabels', { default: true })
</script>

<template>
  <div class="graph-controls">
    <label class="graph-controls__slider">
      연관도 임계값 <strong>{{ minScore.toFixed(2) }}</strong>
      <input v-model.number="minScore" type="range" min="0.1" max="0.9" step="0.05" />
    </label>
    <label class="graph-controls__toggle">
      <input v-model="showLabels" type="checkbox" />
      파일명 라벨 표시
    </label>
  </div>
</template>

<style scoped lang="scss">
.graph-controls {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-wrap: wrap;
  margin-bottom: var(--space-5);
  font-size: var(--text-sm);
}

.graph-controls__slider {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-secondary);

  strong {
    color: var(--color-accent-600);
    font-variant-numeric: tabular-nums;
    min-width: 34px;
  }

  input[type='range'] {
    accent-color: var(--color-accent-500);
    width: 160px;
  }
}

.graph-controls__toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);

  input {
    accent-color: var(--color-accent-500);
  }
}
</style>
