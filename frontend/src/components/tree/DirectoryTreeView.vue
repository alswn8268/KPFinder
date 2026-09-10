<script setup lang="ts">
import type { TreeNode } from '@/api/types'
import DirectoryTreeNode from '@/components/tree/DirectoryTreeNode.vue'

defineProps<{ root: TreeNode }>()
</script>

<template>
  <ul class="directory-tree">
    <DirectoryTreeNode :node="root" :depth="0" />
  </ul>
</template>

<style scoped lang="scss">
.directory-tree {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-2);
  background: var(--color-surface);
}
</style>
