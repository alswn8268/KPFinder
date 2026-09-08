<script setup lang="ts">
import { ref } from 'vue'

import type { DuplicateGroup } from '@/api/types'
import BaseCard from '@/components/base/BaseCard.vue'

defineProps<{ groups: DuplicateGroup[] }>()

const openHashes = ref<Set<string>>(new Set())

function toggle(hash: string) {
  if (openHashes.value.has(hash)) openHashes.value.delete(hash)
  else openHashes.value.add(hash)
}

function formatSize(bytes: number): string {
  return `${(bytes / 1024).toFixed(1)} KB`
}
</script>

<template>
  <div class="dup-list">
    <BaseCard v-for="g in groups" :key="g.hash" padding="sm" class="dup-list__group">
      <button class="dup-list__toggle" @click="toggle(g.hash)">
        <span>동일 파일 {{ g.files.length }}개 — {{ g.files[0].name }}</span>
        <span class="dup-list__chevron" :class="{ 'is-open': openHashes.has(g.hash) }">›</span>
      </button>
      <Transition name="rise">
        <ul v-if="openHashes.has(g.hash)" class="dup-list__files">
          <li v-for="f in g.files" :key="f.relative_path">
            <code>{{ f.relative_path }}</code>
            <span class="muted">{{ formatSize(f.size) }} · {{ new Date(f.modified).toLocaleDateString('ko-KR') }}</span>
          </li>
        </ul>
      </Transition>
    </BaseCard>
  </div>
</template>

<style scoped lang="scss">
.dup-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.dup-list__toggle {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: var(--weight-medium);
  font-size: var(--text-sm);
}

.dup-list__chevron {
  transition: transform var(--duration-base) var(--ease-out);
  color: var(--color-text-tertiary);
  &.is-open {
    transform: rotate(90deg);
  }
}

.dup-list__files {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--text-sm);

  li {
    display: flex;
    justify-content: space-between;
    gap: var(--space-3);
  }

  code {
    font-family: var(--font-mono);
    font-size: 12.5px;
  }
}

.muted {
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
  white-space: nowrap;
}
</style>
