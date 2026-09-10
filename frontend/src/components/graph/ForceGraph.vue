<script setup lang="ts">
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from 'd3-force'
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import type { GraphData } from '@/api/types'
import EmptyState from '@/components/base/EmptyState.vue'

const props = withDefaults(defineProps<{ data: GraphData; height?: number; showLabels?: boolean }>(), {
  height: 460,
  showLabels: true,
})

interface SimNode extends SimulationNodeDatum {
  id: string
  ext: string
  size: number
  file_count: number
}
interface SimLink extends SimulationLinkDatum<SimNode> {
  weight: number
}

const containerRef = ref<HTMLDivElement | null>(null)
const width = ref(760)
const positions = reactive<Record<string, { x: number; y: number }>>({})

const EXT_COLORS = ['#5B4FE9', '#0EA5A0', '#E8515A', '#2563EB', '#D97706', '#DB2777', '#059669', '#7C3AED']
const extOrder: string[] = []
const nodeColor = reactive<Record<string, string>>({})

let simulation: ReturnType<typeof forceSimulation<SimNode, SimLink>> | null = null

function colorForExt(ext: string): string {
  let idx = extOrder.indexOf(ext)
  if (idx === -1) {
    extOrder.push(ext)
    idx = extOrder.length - 1
  }
  return EXT_COLORS[idx % EXT_COLORS.length]
}

function nodeRadius(node: { size: number; file_count: number }): number {
  const base = node.file_count ? 8 + node.file_count * 1.6 : 6
  return Math.min(base + Math.min(node.size, 200_000) / 40_000, 26)
}

function buildSimulation() {
  simulation?.stop()
  const simNodes: SimNode[] = props.data.nodes.map((n) => ({ ...n }))
  const simLinks: SimLink[] = props.data.edges.map((e) => ({ source: e.source, target: e.target, weight: e.weight }))

  simNodes.forEach((n) => {
    nodeColor[n.id] = n.ext ? colorForExt(n.ext) : 'var(--color-accent-500)'
  })

  simulation = forceSimulation(simNodes)
    .force(
      'link',
      forceLink<SimNode, SimLink>(simLinks)
        .id((d) => d.id)
        .distance(64)
        .strength((l) => 0.1 + l.weight * 0.4),
    )
    .force('charge', forceManyBody().strength(-110))
    .force('center', forceCenter(width.value / 2, props.height / 2))
    .force('collide', forceCollide((d) => nodeRadius(d as SimNode) + 4))
    .on('tick', () => {
      for (const n of simNodes) {
        positions[n.id] = { x: n.x ?? 0, y: n.y ?? 0 }
      }
    })
}

onMounted(() => {
  if (containerRef.value) width.value = containerRef.value.clientWidth || width.value
  buildSimulation()
})

onBeforeUnmount(() => simulation?.stop())

watch(
  () => props.data,
  () => buildSimulation(),
)
</script>

<template>
  <div ref="containerRef" class="force-graph">
    <EmptyState
      v-if="data.nodes.length === 0"
      title="표시할 연관 관계가 없습니다."
      description="임계값을 낮추거나 AI 분석을 먼저 실행해보세요."
      icon="🕸️"
    />
    <svg v-else :width="width" :height="height" class="force-graph__svg">
      <line
        v-for="(e, i) in data.edges"
        :key="i"
        class="force-graph__edge"
        :x1="positions[e.source]?.x ?? 0"
        :y1="positions[e.source]?.y ?? 0"
        :x2="positions[e.target]?.x ?? 0"
        :y2="positions[e.target]?.y ?? 0"
        :style="{ opacity: 0.12 + e.weight * 0.55, strokeWidth: 1 + e.weight * 2.5 }"
      />
      <g
        v-for="n in data.nodes"
        :key="n.id"
        class="force-graph__node"
        :transform="`translate(${positions[n.id]?.x ?? 0}, ${positions[n.id]?.y ?? 0})`"
      >
        <circle :r="nodeRadius(n)" :fill="nodeColor[n.id]" />
        <text v-if="showLabels" class="force-graph__label" :y="nodeRadius(n) + 12">
          {{ n.id.split('/').pop() }}
        </text>
        <title>{{ n.id }}</title>
      </g>
    </svg>
  </div>
</template>

<style scoped lang="scss">
.force-graph {
  width: 100%;
}

.force-graph__svg {
  width: 100%;
}

.force-graph__edge {
  stroke: var(--color-text-tertiary);
}

.force-graph__node circle {
  stroke: var(--color-surface);
  stroke-width: 1.5px;
  transition: r var(--duration-base) var(--ease-out);
}

.force-graph__node:hover circle {
  filter: brightness(1.15);
}

.force-graph__label {
  font-size: 9px;
  text-anchor: middle;
  fill: var(--color-text-secondary);
  pointer-events: none;
}
</style>
