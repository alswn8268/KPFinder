<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { restoreVersion } from '@/api/versions'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import MetricStat from '@/components/base/MetricStat.vue'
import PlanTable from '@/components/data/PlanTable.vue'
import { FINAL_STATE_TONE } from '@/constants/status'
import { useApplyStore } from '@/stores/apply'
import { useEditStore } from '@/stores/edit'
import { useScanStore } from '@/stores/scan'
import { useUiStore } from '@/stores/ui'

const scan = useScanStore()
const edit = useEditStore()
const applyStore = useApplyStore()
const ui = useUiStore()
const router = useRouter()

const confirmChecked = ref(false)
const restoringNow = ref(false)

onMounted(async () => {
  if (!Object.keys(edit.merged).length) await edit.refresh()
  await applyStore.refreshPlan()
})

const statusCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const row of edit.finalState) counts.set(row['상태'], (counts.get(row['상태']) ?? 0) + 1)
  return counts
})

async function onApply() {
  try {
    const result = await applyStore.apply('')
    if (result.moved_count === applyStore.plan.length) {
      ui.pushToast(`${result.moved_count}개 파일 이동을 완료했습니다.`, 'success')
    } else if (result.moved_count === 0) {
      ui.pushToast('이동 중 오류가 발생해 모든 변경 사항을 자동으로 복구했습니다. 원본 상태가 유지됩니다.', 'error')
    } else {
      ui.pushToast(`${result.moved_count}개 파일만 이동되었습니다(일부는 변경 감지 등으로 건너뜀).`, 'warning')
    }
    confirmChecked.value = false
    await scan.scan(scan.root)
  } catch {
    // 인터셉터가 처리
  }
}

async function onRestoreNow() {
  if (!applyStore.lastResult) return
  restoringNow.value = true
  try {
    const result = await restoreVersion(scan.root, applyStore.lastResult.version.version_id)
    ui.pushToast(`${result.restored_count}개 파일을 원래 위치로 되돌렸습니다.`, 'success')
    await scan.scan(scan.root)
    applyStore.reset()
  } finally {
    restoringNow.value = false
  }
}
</script>

<template>
  <div class="apply-view">
    <BaseCard>
      <template #header>적용 결과 요약(예상)</template>
      <div class="apply-view__metrics">
        <MetricStat
          v-for="[status, count] in statusCounts"
          :key="status"
          :label="status"
          :value="count"
          :tone="FINAL_STATE_TONE[status] === 'accent' ? 'accent' : FINAL_STATE_TONE[status] === 'danger' ? 'danger' : 'neutral'"
        />
      </div>
    </BaseCard>

    <BaseCard v-if="edit.rejected.length" class="apply-view__warning-card">
      <p class="apply-view__warning-title">안전성 검사에서 제외된 항목 {{ edit.rejected.length }}건</p>
      <ul>
        <li v-for="r in edit.rejected" :key="r.src"><code>{{ r.src }}</code> → <code>{{ r.dst }}</code>: {{ r.reason }}</li>
      </ul>
    </BaseCard>

    <BaseCard v-if="!applyStore.lastResult">
      <template #header>이동 계획 ({{ applyStore.plan.length }}개 파일)</template>
      <PlanTable :plan="applyStore.plan" />

      <div class="apply-view__safety">
        <p><strong>{{ applyStore.plan.length }}개 파일</strong>을 위에 표시된 최종 경로로 이동합니다.</p>
        <ul>
          <li>기존 파일은 절대 덮어쓰지 않습니다.</li>
          <li>이동 중 오류가 발생하면 이미 이동한 파일을 자동으로 복구합니다.</li>
          <li>적용 후 '버전 관리'에서 이 작업을 언제든 되돌릴 수 있습니다.</li>
        </ul>
      </div>

      <label class="apply-view__confirm">
        <input v-model="confirmChecked" type="checkbox" />
        위 이동 계획을 확인했으며, 실제로 파일을 이동하는 데 동의합니다.
      </label>

      <BaseButton
        size="lg"
        :disabled="!confirmChecked || applyStore.plan.length === 0"
        :loading="applyStore.applying"
        @click="onApply"
      >
        🚀 적용 (실제 파일 이동)
      </BaseButton>
    </BaseCard>

    <Transition name="rise">
      <BaseCard v-if="applyStore.lastResult" class="apply-view__result">
        <template #header>적용 완료</template>
        <div class="apply-view__result-metrics">
          <BaseBadge tone="success">이동 성공 {{ applyStore.lastResult.moved_count }}개</BaseBadge>
          <BaseBadge tone="neutral">계획 {{ applyStore.lastResult.plan_size }}개</BaseBadge>
        </div>
        <p class="apply-view__result-hint">문제가 있다면 지금 바로 되돌리거나, 버전 관리 탭에서 언제든 되돌릴 수 있습니다.</p>
        <div class="apply-view__result-actions">
          <BaseButton variant="danger" :loading="restoringNow" @click="onRestoreNow">지금 되돌리기</BaseButton>
          <BaseButton variant="secondary" @click="router.push({ name: 'versions' })">버전 관리로 이동</BaseButton>
        </div>
      </BaseCard>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
.apply-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.apply-view__metrics {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.apply-view__warning-card {
  border-color: var(--color-warning);
}

.apply-view__warning-title {
  font-weight: var(--weight-semibold);
  color: var(--color-warning);
  margin-bottom: var(--space-2);
}

.apply-view__safety {
  margin: var(--space-5) 0;
  padding: var(--space-4);
  background: var(--color-info-soft);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);

  ul {
    margin-top: var(--space-2);
    padding-left: var(--space-5);
    list-style: disc;
    color: var(--color-text-secondary);
  }
}

.apply-view__confirm {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  margin-bottom: var(--space-4);

  input {
    accent-color: var(--color-accent-500);
  }
}

.apply-view__result-metrics {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.apply-view__result-hint {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-4);
}

.apply-view__result-actions {
  display: flex;
  gap: var(--space-3);
}
</style>
