<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { copyStructureOnly } from '@/api/structureCopy'
import BarChart from '@/components/charts/BarChart.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import MetricStat from '@/components/base/MetricStat.vue'
import FileTable from '@/components/data/FileTable.vue'
import DuplicateGroupList from '@/components/data/DuplicateGroupList.vue'
import { useScanStore } from '@/stores/scan'
import { useUiStore } from '@/stores/ui'

const scan = useScanStore()
const ui = useUiStore()
const router = useRouter()

const query = ref('')
const selectedExt = ref('')
const copyDest = ref('')
const copying = ref(false)

const allExts = computed(() => {
  const set = new Set(scan.entries.map((e) => e.ext || '(없음)'))
  return Array.from(set).sort()
})

const filtered = computed(() => {
  let items = scan.entries
  if (selectedExt.value) {
    items = items.filter((e) => (e.ext || '(없음)') === selectedExt.value)
  }
  if (query.value.trim()) {
    const q = query.value.trim().toLowerCase()
    items = items.filter(
      (e) =>
        e.relative_path.toLowerCase().includes(q) ||
        e.name.toLowerCase().includes(q) ||
        e.summary.toLowerCase().includes(q),
    )
  }
  return items
})

const extCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const e of filtered.value) {
    const key = e.ext || '(없음)'
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return Array.from(counts.entries())
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8)
})

const folderCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const e of filtered.value) {
    const parts = e.relative_path.replace(/\\/g, '/').split('/')
    const folder = parts.length > 1 ? parts.slice(0, -1).join('/') : '(최상위)'
    counts.set(folder, (counts.get(folder) ?? 0) + 1)
  }
  return Array.from(counts.entries())
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8)
})

const wastedKb = computed(() =>
  scan.duplicateGroups.reduce((sum, g) => sum + (g.files[0]?.size ?? 0) * (g.files.length - 1), 0) / 1024,
)

async function onCopyStructure() {
  if (!copyDest.value.trim()) {
    ui.pushToast('생성할 위치를 입력하세요.', 'warning')
    return
  }
  copying.value = true
  try {
    const result = await copyStructureOnly(scan.entries, copyDest.value.trim())
    ui.pushToast(`${result.count}개 폴더를 만들었습니다: ${copyDest.value}`, 'success')
    if (result.skipped.length) {
      ui.pushToast(`일부 폴더는 건너뛰었습니다: ${result.skipped.join(', ')}`, 'warning')
    }
  } finally {
    copying.value = false
  }
}
</script>

<template>
  <div class="scan-result">
    <div class="scan-result__metrics">
      <MetricStat label="전체 파일" :value="scan.totalFiles" tone="accent" />
      <MetricStat label="완전 중복 그룹" :value="scan.duplicateGroups.length" tone="warning" />
      <MetricStat label="읽기 오류" :value="scan.scanErrors.length" :tone="scan.scanErrors.length ? 'danger' : 'neutral'" />
      <MetricStat label="절감 가능 용량" :value="`${wastedKb.toFixed(1)} KB`" tone="neutral" />
    </div>

    <BaseCard>
      <template #header>🔍 검색</template>
      <div class="scan-result__search">
        <input v-model="query" type="text" placeholder="파일명 / 경로 / 요약 내용으로 검색" />
        <select v-model="selectedExt">
          <option value="">전체 확장자</option>
          <option v-for="ext in allExts" :key="ext" :value="ext">{{ ext }}</option>
        </select>
      </div>
      <p class="scan-result__count">전체 {{ scan.totalFiles }}개 중 {{ filtered.length }}개 표시</p>
      <FileTable :entries="filtered" />
    </BaseCard>

    <div class="scan-result__grid">
      <BaseCard>
        <template #header>확장자별 파일 수</template>
        <BarChart :data="extCounts" />
      </BaseCard>
      <BaseCard>
        <template #header>폴더별 파일 수</template>
        <BarChart :data="folderCounts" />
      </BaseCard>
    </div>

    <BaseCard v-if="scan.duplicateGroups.length">
      <template #header>🧬 완전 중복 파일</template>
      <DuplicateGroupList :groups="scan.duplicateGroups" />
    </BaseCard>

    <BaseCard>
      <template #header>📐 폴더 구조만 복사 (내용 없이)</template>
      <p class="scan-result__hint">파일 내용 없이 하위 폴더 체계만 다른 위치에 그대로 만듭니다.</p>
      <div class="scan-result__copy-row">
        <input v-model="copyDest" type="text" placeholder="생성할 위치(대상 폴더)" />
        <BaseButton variant="secondary" :loading="copying" @click="onCopyStructure">구조만 복사하기</BaseButton>
      </div>
    </BaseCard>

    <div class="scan-result__next">
      <BaseButton size="lg" @click="router.push({ name: 'classify' })">다음: 분류 실행 →</BaseButton>
    </div>
  </div>
</template>

<style scoped lang="scss">
.scan-result {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.scan-result__metrics {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.scan-result__search {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-3);

  input {
    flex: 1;
    padding: var(--space-3);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
  }

  select {
    padding: var(--space-3);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
  }
}

.scan-result__count {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-3);
}

.scan-result__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
}

.scan-result__hint {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-3);
}

.scan-result__copy-row {
  display: flex;
  gap: var(--space-3);

  input {
    flex: 1;
    padding: var(--space-3);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
  }
}

.scan-result__next {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 860px) {
  .scan-result__grid {
    grid-template-columns: 1fr;
  }
}
</style>
