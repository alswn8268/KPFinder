<script setup lang="ts">
import { ref } from 'vue'

import type { TreeNode } from '@/api/types'

const props = defineProps<{ node: TreeNode; depth?: number }>()
const expanded = ref((props.depth ?? 0) < 1)

function displayName(id: string): string {
  return id === '(최상위)' ? id : id.split('/').pop() ?? id
}
</script>

<template>
  <li class="tree-node">
    <button
      class="tree-node__row"
      :class="{ 'is-leaf': node.children.length === 0 }"
      :style="{ paddingLeft: `${(depth ?? 0) * 16}px` }"
      @click="node.children.length && (expanded = !expanded)"
    >
      <span v-if="node.children.length" class="tree-node__chevron" :class="{ 'is-open': expanded }">›</span>
      <span v-else class="tree-node__chevron tree-node__chevron--spacer" />
      <span class="tree-node__icon" aria-hidden="true">{{ node.children.length ? '📁' : '📄' }}</span>
      <span class="tree-node__name">{{ displayName(node.id) }}</span>
      <span class="tree-node__count">{{ node.file_count }}</span>
    </button>
    <Transition name="rise">
      <ul v-if="expanded && node.children.length" class="tree-node__children">
        <DirectoryTreeNode v-for="child in node.children" :key="child.id" :node="child" :depth="(depth ?? 0) + 1" />
      </ul>
    </Transition>
  </li>
</template>

<style scoped lang="scss">
.tree-node__row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 6px var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  transition: background-color var(--duration-fast) var(--ease-out);

  &:hover {
    background: var(--color-neutral-soft);
  }

  &.is-leaf {
    color: var(--color-text-secondary);
  }
}

.tree-node__chevron {
  width: 14px;
  color: var(--color-text-tertiary);
  transition: transform var(--duration-fast) var(--ease-out);
  &.is-open {
    transform: rotate(90deg);
  }
  &--spacer {
    visibility: hidden;
  }
}

.tree-node__name {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-node__count {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
}

.tree-node__children {
  overflow: hidden;
}
</style>
