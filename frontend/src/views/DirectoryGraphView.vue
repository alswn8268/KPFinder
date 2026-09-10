<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { fetchDirectoryRelationGraph, fetchDirectoryTree } from '@/api/graphs'
import BaseCard from '@/components/base/BaseCard.vue'
import SkeletonLoader from '@/components/base/SkeletonLoader.vue'
import GraphControls from '@/components/graph/GraphControls.vue'
import ForceGraph from '@/components/graph/ForceGraph.vue'
import DirectoryTreeView from '@/components/tree/DirectoryTreeView.vue'
import type { GraphData, TreeNode } from '@/api/types'
import { useScanStore } from '@/stores/scan'

const scan = useScanStore()
const tree = ref<TreeNode | null>(null)
const relationGraph = ref<GraphData>({ nodes: [], edges: [] })
const minScore = ref(0.4)
const showLabels = ref(true)
const loading = ref(false)

async function loadTree() {
  tree.value = await fetchDirectoryTree(scan.entries)
}

async function loadRelation() {
  loading.value = true
  try {
    relationGraph.value = await fetchDirectoryRelationGraph(scan.entries, minScore.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTree()
  loadRelation()
})

watch(minScore, () => loadRelation())
</script>

<template>
  <div class="dir-graph">
    <p class="dir-graph__intro">
      Obsidian의 그래프 뷰에서 착안한 폴더 단위 시각화입니다. 왼쪽은 폴더 계층 구조, 오른쪽은
      서로 다른 폴더에 흩어진 파일들이 내용상 얼마나 비슷한지를 보여줍니다(병합 후보 힌트).
    </p>
    <div class="dir-graph__grid">
      <BaseCard>
        <template #header>폴더 구조도</template>
        <DirectoryTreeView v-if="tree" :root="tree" />
      </BaseCard>
      <BaseCard>
        <template #header>폴더 간 연관도</template>
        <GraphControls v-model:min-score="minScore" v-model:show-labels="showLabels" />
        <SkeletonLoader v-if="loading" :lines="4" />
        <ForceGraph v-else :data="relationGraph" :show-labels="showLabels" />
      </BaseCard>
    </div>
  </div>
</template>

<style scoped lang="scss">
.dir-graph__intro {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  max-width: 80ch;
  margin-bottom: var(--space-6);
}

.dir-graph__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
  align-items: start;
}

@media (max-width: 900px) {
  .dir-graph__grid {
    grid-template-columns: 1fr;
  }
}
</style>
