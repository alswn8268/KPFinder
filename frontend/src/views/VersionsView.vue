<script setup lang="ts">
import { onMounted } from 'vue'

import BaseCard from '@/components/base/BaseCard.vue'
import EmptyState from '@/components/base/EmptyState.vue'
import VersionCard from '@/components/data/VersionCard.vue'
import { useScanStore } from '@/stores/scan'
import { useUiStore } from '@/stores/ui'
import { useVersionsStore } from '@/stores/versions'

const scan = useScanStore()
const versions = useVersionsStore()
const ui = useUiStore()

onMounted(() => versions.fetch(scan.root))

async function onRestore(versionId: string) {
  const result = await versions.restore(scan.root, versionId)
  ui.pushToast(`${result.restored_count}개 파일을 원래 위치로 되돌렸습니다.`, 'success')
}
</script>

<template>
  <div class="versions-view">
    <p class="versions-view__intro">
      '적용'을 누를 때마다 새로운 버전이 기록됩니다. 더 최근 버전이 남아 있으면 과거 버전은
      순서상 먼저 되돌릴 수 없습니다.
    </p>
    <BaseCard v-if="versions.versions.length === 0">
      <EmptyState title="이 폴더에 대해 아직 적용된 정리 작업이 없습니다." icon="🕘" />
    </BaseCard>
    <div v-else class="versions-view__list">
      <TransitionGroup name="list">
        <VersionCard
          v-for="v in [...versions.versions].reverse()"
          :key="v.version_id"
          :version="v"
          :restoring="versions.restoring === v.version_id"
          @restore="onRestore"
        />
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped lang="scss">
.versions-view__intro {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-6);
}

.versions-view__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>
