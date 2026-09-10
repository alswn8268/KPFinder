<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ data: { label: string; value: number }[] }>()

const max = computed(() => Math.max(...props.data.map((d) => d.value), 1))
</script>

<template>
  <div class="bar-chart">
    <div v-for="d in data" :key="d.label" class="bar-chart__row">
      <span class="bar-chart__label" :title="d.label">{{ d.label }}</span>
      <div class="bar-chart__track">
        <div class="bar-chart__fill" :style="{ width: (d.value / max) * 100 + '%' }" />
      </div>
      <span class="bar-chart__value">{{ d.value }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.bar-chart__row {
  display: grid;
  grid-template-columns: 120px 1fr 32px;
  align-items: center;
  gap: var(--space-3);
}

.bar-chart__label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-chart__track {
  height: 10px;
  border-radius: var(--radius-full);
  background: var(--color-neutral-soft);
  overflow: hidden;
}

.bar-chart__fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--color-accent-400), var(--color-accent-600));
  transition: width var(--duration-slow) var(--ease-out);
}

.bar-chart__value {
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
  color: var(--color-text-tertiary);
  text-align: right;
}
</style>
