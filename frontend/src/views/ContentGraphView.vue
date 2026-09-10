<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { fetchContentGraph } from '@/api/graphs'
import type { GraphData } from '@/api/types'
import BaseCard from '@/components/base/BaseCard.vue'
import SkeletonLoader from '@/components/base/SkeletonLoader.vue'
import GraphControls from '@/components/graph/GraphControls.vue'
import ForceGraph from '@/components/graph/ForceGraph.vue'
import { useScanStore } from '@/stores/scan'
import { useUiStore } from '@/stores/ui'

const scan = useScanStore()
const ui = useUiStore()
const graph = ref<GraphData>({ nodes: [], edges: [] })
const minScore = ref(0.35)
const showLabels = ref(true)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    graph.value = await fetchContentGraph(scan.entries, minScore.value, true)
  } catch (err: any) {
    if (err?.response?.status === 422) {
      ui.pushToast(err.response.data.detail, 'warning')
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(minScore, load)
</script>

<template>
  <div class="content-graph">
    <p class="content-graph__intro">
      노드 = 파일, 선 = 파일명/AI 요약 유사도. 임베딩 모델 없이 가볍게 추정한 값이라 완벽하지는
      않지만, 어떤 문서끼리 관련 있어 보이는지 한눈에 훑어보는 용도입니다.
    </p>
    <BaseCard>
      <GraphControls v-model:min-score="minScore" v-model:show-labels="showLabels" />
      <SkeletonLoader v-if="loading" :lines="5" />
      <ForceGraph v-else :data="graph" :show-labels="showLabels" :height="560" />
      <p class="content-graph__count">임계값 {{ minScore.toFixed(2) }} 이상인 연결 {{ graph.edges.length }}개</p>
    </BaseCard>
  </div>
</template>

<style scoped lang="scss">
.content-graph__intro {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  max-width: 80ch;
  margin-bottom: var(--space-6);
}

.content-graph__count {
  margin-top: var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}
</style>
