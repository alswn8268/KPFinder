<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { downloadExcelReport, downloadJsonReport, fetchHtmlReport, openHtmlReportInNewTab } from '@/api/report'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import ProposalEditTable from '@/components/data/ProposalEditTable.vue'
import FinalStateTable from '@/components/data/FinalStateTable.vue'
import BeforeAfterTree from '@/components/tree/BeforeAfterTree.vue'
import { useClassificationStore } from '@/stores/classification'
import { useEditStore } from '@/stores/edit'
import { useScanStore } from '@/stores/scan'
import { useTemplateStore } from '@/stores/template'
import { useUiStore } from '@/stores/ui'

const scan = useScanStore()
const classification = useClassificationStore()
const edit = useEditStore()
const template = useTemplateStore()
const ui = useUiStore()
const router = useRouter()

onMounted(() => {
  if (!Object.keys(edit.valid).length) edit.refresh()
})

function reportPayload() {
  return {
    entries: scan.entries,
    duplicate_groups: scan.duplicateGroups,
    proposal: {
      categories: classification.categories,
      assignments: classification.assignments,
      notes: classification.notes,
    },
    similar_docs: classification.similarDocs,
    final_state: edit.finalState,
    env_items: [],
    model: classification.model,
    template_name: template.active?.name ?? '',
    template_version: template.active?.version ?? '',
  }
}

async function onDownloadJson() {
  await downloadJsonReport(reportPayload())
  ui.pushToast('JSON 리포트를 다운로드했습니다.', 'success')
}

async function onDownloadExcel() {
  await downloadExcelReport(reportPayload())
  ui.pushToast('엑셀 리포트를 다운로드했습니다.', 'success')
}

async function onOpenHtml() {
  const html = await fetchHtmlReport(reportPayload())
  openHtmlReportInNewTab(html)
}
</script>

<template>
  <div class="proposal-view">
    <BaseCard>
      <template #header>📝 제안 편집</template>
      <ProposalEditTable />
    </BaseCard>

    <BaseCard v-if="edit.rejected.length">
      <template #header>안전성 검사에서 제외된 항목</template>
      <ul class="proposal-view__rejected">
        <li v-for="r in edit.rejected" :key="r.src">
          <code>{{ r.src }}</code> → <code>{{ r.dst }}</code>: {{ r.reason }}
        </li>
      </ul>
    </BaseCard>

    <BaseCard>
      <template #header>Before / After 폴더 구조 비교</template>
      <BeforeAfterTree :before="edit.treeBefore" :after="edit.treeAfter" />
    </BaseCard>

    <BaseCard>
      <template #header>최종 상태 미리보기 (실제로 적용됐을 때)</template>
      <FinalStateTable :rows="edit.finalState" />
    </BaseCard>

    <div class="proposal-view__actions">
      <div class="proposal-view__reports">
        <BaseButton variant="secondary" @click="onDownloadJson">📥 JSON 리포트</BaseButton>
        <BaseButton variant="secondary" @click="onDownloadExcel">📊 엑셀 리포트</BaseButton>
        <BaseButton variant="secondary" @click="onOpenHtml">🖨️ HTML 리포트(인쇄/PDF)</BaseButton>
      </div>
      <BaseButton size="lg" @click="router.push({ name: 'apply' })">다음: 적용 →</BaseButton>
    </div>
  </div>
</template>

<style scoped lang="scss">
.proposal-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.proposal-view__rejected {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-danger);

  code {
    font-family: var(--font-mono);
    font-size: 12.5px;
  }
}

.proposal-view__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-4);
}

.proposal-view__reports {
  display: flex;
  gap: var(--space-3);
}
</style>
