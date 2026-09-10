<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import { listRecommendedModels, pullModel } from '@/api/models'
import type { PullProgressEvent, RecommendedModelInfo } from '@/api/types'
import { SUMMARY_STATUS_LABEL } from '@/constants/status'
import { useClassificationStore } from '@/stores/classification'
import { useEditStore } from '@/stores/edit'
import { useEnvStore } from '@/stores/env'
import { useScanStore } from '@/stores/scan'
import { useTemplateStore } from '@/stores/template'
import { useUiStore } from '@/stores/ui'

// 실측 리허설(2026-09-08) 기준: 파일 요약 평균 약 8~20초, 폴더 구조 제안은 파일당 평균 약 26초.
// 실제 소요 시간을 예측할 순 없지만, 이 값으로 "대략 이 정도" 감을 주는 정도로만 쓴다.
const SECONDS_PER_STRUCTURE_FILE = 26

const scan = useScanStore()
const classification = useClassificationStore()
const template = useTemplateStore()
const env = useEnvStore()
const edit = useEditStore()
const ui = useUiStore()
const router = useRouter()

const ollamaOk = computed(() => env.ollamaConnected())
const effectiveUseAi = computed(() => classification.useAi && ollamaOk.value)

const summarized = computed(() => scan.entries.filter((e) => e.summary_status !== 'pending'))

const proposingElapsed = ref(0)
let proposingTimer: number | undefined

watch(
  () => classification.proposingStructure,
  (active) => {
    if (active) {
      proposingElapsed.value = 0
      proposingTimer = window.setInterval(() => {
        proposingElapsed.value += 1
      }, 1000)
    } else if (proposingTimer !== undefined) {
      window.clearInterval(proposingTimer)
      proposingTimer = undefined
    }
  },
)

onBeforeUnmount(() => {
  if (proposingTimer !== undefined) window.clearInterval(proposingTimer)
})

function formatModelLabel(m: { name: string; size_mb: number; parameter_size: string }): string {
  const size = m.size_mb >= 1024 ? `${(m.size_mb / 1024).toFixed(1)}GB` : `${m.size_mb}MB`
  return `${m.name} · ${size}${m.parameter_size ? ` · ${m.parameter_size}` : ''}`
}

function formatSeconds(s: number): string {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}분 ${sec}초` : `${sec}초`
}

onMounted(() => {
  if (ollamaOk.value) classification.loadAvailableModels()
})

const showDownload = ref(false)
const recommendedModels = ref<RecommendedModelInfo[]>([])
const downloadingName = ref<string | null>(null)
const downloadStatus = ref('')
const downloadPct = ref<number | null>(null)

async function loadRecommended() {
  try {
    recommendedModels.value = await listRecommendedModels()
  } catch {
    // 목록을 못 불러와도(예: Ollama 연결 끊김) 무시 — 버튼을 눌렀을 때 다시 시도된다
  }
}

watch(showDownload, (open) => {
  if (open && !recommendedModels.value.length) loadRecommended()
})

function formatMb(bytes: number): string {
  return `${Math.round(bytes / 1024 / 1024)}MB`
}

function onPullProgress(evt: PullProgressEvent) {
  if (evt.status === 'downloading' && evt.total && evt.completed !== undefined) {
    downloadStatus.value = `다운로드 중 (${formatMb(evt.completed)} / ${formatMb(evt.total)})`
    downloadPct.value = Math.round((evt.completed / evt.total) * 100)
  } else {
    downloadStatus.value = evt.status
  }
}

async function onDownload(m: RecommendedModelInfo) {
  downloadingName.value = m.name
  downloadStatus.value = '다운로드 준비 중…'
  downloadPct.value = null
  try {
    await pullModel(m.name, onPullProgress)
    ui.pushToast(`'${m.label}' 모델을 받았습니다. 목록에서 바로 골라 쓸 수 있어요.`, 'success')
    await classification.loadAvailableModels()
    classification.selectModel(m.name)
    await loadRecommended()
  } catch (err) {
    ui.pushToast(`다운로드에 실패했습니다: ${err instanceof Error ? err.message : err}`, 'error')
  } finally {
    downloadingName.value = null
  }
}

async function onClassify() {
  if (!template.active) await template.loadDefault()
  try {
    await classification.runClassification(
      scan.entries,
      scan.root,
      template.active!,
      effectiveUseAi.value,
    )
    edit.reset()
    await edit.refresh()
    ui.pushToast(
      effectiveUseAi.value
        ? '규칙 + AI 분류가 완료되었습니다.'
        : 'AI 없이 규칙 기반으로만 분류했습니다. 규칙에 걸리지 않은 파일은 제안 편집에서 직접 지정하세요.',
      'success',
    )
  } catch {
    // 인터셉터가 에러 토스트 처리
  }
}

function goToProposal() {
  router.push({ name: 'proposal' })
}
</script>

<template>
  <div class="classify-view">
    <BaseCard>
      <template #header>🤖 분류 실행</template>
      <div class="classify-view__controls">
        <label class="classify-view__field classify-view__field--grow">
          <span>Ollama 모델 <span class="classify-view__hint">(용량이 작을수록 사양 낮은 PC에 유리)</span></span>
          <div class="classify-view__model-row">
            <select
              v-if="classification.availableModels.length"
              :value="classification.model"
              :disabled="!ollamaOk"
              @change="classification.selectModel(($event.target as HTMLSelectElement).value)"
            >
              <option v-for="m in classification.availableModels" :key="m.name" :value="m.name">
                {{ formatModelLabel(m) }}
              </option>
            </select>
            <input v-else v-model="classification.model" type="text" :disabled="!ollamaOk" />
            <button
              type="button"
              class="classify-view__refresh"
              :disabled="!ollamaOk || classification.modelsLoading"
              title="설치된 모델 목록 다시 불러오기"
              @click="classification.loadAvailableModels()"
            >
              {{ classification.modelsLoading ? '…' : '↻' }}
            </button>
          </div>
        </label>
        <label class="classify-view__toggle">
          <input v-model="classification.useAi" type="checkbox" :disabled="!ollamaOk" />
          AI 분류 사용
        </label>
      </div>
      <p class="classify-view__notice classify-view__notice--info">
        PC 사양이 낮다면 <b>"AI 분류 사용"을 끄고 규칙 기반으로만</b> 정리하거나, 위 목록에서
        가장 용량이 작은 모델을 고르세요. 둘 다 언제든 다시 켤 수 있습니다.
      </p>
      <p v-if="!ollamaOk" class="classify-view__notice">
        Ollama에 연결할 수 없습니다. 규칙 기반 분류만으로도 계속 사용할 수 있습니다.
      </p>

      <button v-if="ollamaOk" type="button" class="classify-view__download-toggle" @click="showDownload = !showDownload">
        {{ showDownload ? '모델 다운로드 닫기' : '📥 사양에 맞는 모델을 아직 안 받으셨나요? — 여기서 바로 받기' }}
      </button>
      <Transition name="rise">
        <div v-if="showDownload" class="classify-view__download">
          <p class="classify-view__download-hint">
            Ollama를 막 설치해 모델이 하나도 없거나, 지금 모델보다 더 가벼운(또는 더 정교한) 모델이
            필요할 때 사양별로 골라 바로 받을 수 있습니다. 다운로드는 이 PC의 Ollama가 직접
            처리하며, 창을 닫아도 계속 진행됩니다.
          </p>
          <div v-if="recommendedModels.length" class="classify-view__download-list">
            <div v-for="m in recommendedModels" :key="m.name" class="classify-view__download-card">
              <div class="classify-view__download-card-head">
                <span class="classify-view__download-tier">{{ m.tier }}</span>
                <strong>{{ m.label }}</strong>
                <span class="classify-view__download-size">약 {{ m.size_gb }}GB</span>
              </div>
              <p class="classify-view__download-desc">{{ m.description }}</p>

              <BaseBadge v-if="m.installed" tone="success" size="sm">✓ 설치됨</BaseBadge>
              <BaseButton
                v-else-if="downloadingName !== m.name"
                variant="secondary"
                size="sm"
                :disabled="downloadingName !== null"
                @click="onDownload(m)"
              >
                다운로드
              </BaseButton>
              <div v-else class="classify-view__download-progress">
                <div class="classify-view__progress-bar" :class="{ 'classify-view__progress-bar--indeterminate': downloadPct === null }">
                  <div
                    v-if="downloadPct !== null"
                    class="classify-view__progress-fill"
                    :style="{ width: `${downloadPct}%` }"
                  />
                  <div v-else class="classify-view__progress-fill classify-view__progress-fill--sweep" />
                </div>
                <p class="classify-view__progress-detail">{{ downloadStatus }}</p>
              </div>
            </div>
          </div>
        </div>
      </Transition>
      <BaseButton :loading="classification.classifying" @click="onClassify">
        {{ effectiveUseAi ? '2️⃣ 분류 실행 (규칙 + AI)' : '2️⃣ 분류 실행 (규칙 기반, AI 미사용)' }}
      </BaseButton>

      <Transition name="rise">
        <div v-if="classification.summarizing && classification.summarizeProgress" class="classify-view__progress">
          <div class="classify-view__progress-head">
            <span>
              규칙에 안 걸린 파일만 AI로 요약 중
              ({{ classification.summarizeProgress.current }}/{{ classification.summarizeProgress.total }})
            </span>
            <span class="classify-view__progress-pct">
              {{ Math.round((classification.summarizeProgress.current / classification.summarizeProgress.total) * 100) }}%
            </span>
          </div>
          <div class="classify-view__progress-bar">
            <div
              class="classify-view__progress-fill"
              :style="{ width: `${(classification.summarizeProgress.current / classification.summarizeProgress.total) * 100}%` }"
            />
          </div>
          <p class="classify-view__progress-detail mono">{{ classification.summarizeProgress.currentFile }}</p>
        </div>
      </Transition>

      <Transition name="rise">
        <div v-if="classification.proposingStructure" class="classify-view__progress">
          <div class="classify-view__progress-head">
            <span>AI가 {{ classification.proposingCount }}개 파일로 폴더 구조를 제안하는 중…</span>
            <span class="classify-view__progress-pct">경과 {{ formatSeconds(proposingElapsed) }}</span>
          </div>
          <div class="classify-view__progress-bar classify-view__progress-bar--indeterminate">
            <div class="classify-view__progress-fill classify-view__progress-fill--sweep" />
          </div>
          <p class="classify-view__progress-detail">
            실측 기준 파일당 평균 약 {{ SECONDS_PER_STRUCTURE_FILE }}초 — 대략 최대
            {{ formatSeconds(classification.proposingCount * SECONDS_PER_STRUCTURE_FILE) }} 정도 예상됩니다.
            하드웨어에 따라 크게 달라질 수 있습니다.
          </p>
        </div>
      </Transition>
    </BaseCard>

    <BaseCard v-if="summarized.length">
      <template #header>파일별 요약</template>
      <table class="classify-view__table">
        <thead>
          <tr>
            <th>경로</th>
            <th>상태</th>
            <th>요약</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in summarized" :key="e.relative_path">
            <td class="mono">{{ e.relative_path }}</td>
            <td><BaseBadge tone="neutral" size="sm">{{ SUMMARY_STATUS_LABEL[e.summary_status] ?? e.summary_status }}</BaseBadge></td>
            <td>{{ e.summary || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </BaseCard>

    <BaseCard v-if="classification.similarDocs.length">
      <template #header>🔎 유사 문서 (버전이 다를 수 있는 파일)</template>
      <ul class="classify-view__similar">
        <li v-for="(pair, i) in classification.similarDocs.slice(0, 20)" :key="i">
          <code>{{ pair.a }}</code> ↔ <code>{{ pair.b }}</code>
          <BaseBadge tone="info" size="sm">유사도 {{ Math.round(pair.score * 100) }}%</BaseBadge>
        </li>
      </ul>
    </BaseCard>

    <BaseCard v-if="classification.hasResult">
      <p v-if="classification.notes">{{ classification.notes }}</p>
      <div class="classify-view__next">
        <BaseButton size="lg" @click="goToProposal">다음: 제안 편집 →</BaseButton>
      </div>
    </BaseCard>
  </div>
</template>

<style scoped lang="scss">
.classify-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.classify-view__controls {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: var(--space-6);
  margin-bottom: var(--space-4);
}

.classify-view__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);

  input,
  select {
    padding: var(--space-2) var(--space-3);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    background: var(--color-bg);
  }

  &--grow {
    flex: 1;
    min-width: 260px;
  }
}

.classify-view__hint {
  font-weight: var(--weight-regular);
  color: var(--color-text-tertiary);
}

.classify-view__model-row {
  display: flex;
  gap: var(--space-2);

  select {
    flex: 1;
    min-width: 0;
  }
}

.classify-view__refresh {
  flex-shrink: 0;
  width: 34px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: 15px;

  &:hover:not(:disabled) {
    color: var(--color-accent-600);
    border-color: var(--color-accent-400);
  }

  &:disabled {
    opacity: 0.5;
  }
}

.classify-view__toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);

  input {
    accent-color: var(--color-accent-500);
  }
}

.classify-view__notice {
  font-size: var(--text-xs);
  color: var(--color-warning);
  margin-bottom: var(--space-3);

  &--info {
    color: var(--color-text-secondary);
    background: var(--color-accent-soft);
    padding: var(--space-3);
    border-radius: var(--radius-md);
  }
}

.classify-view__download-toggle {
  display: block;
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-accent-600);
  margin-bottom: var(--space-3);

  &:hover {
    text-decoration: underline;
  }
}

.classify-view__download {
  margin-bottom: var(--space-4);
}

.classify-view__download-hint {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-3);
}

.classify-view__download-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-3);
}

.classify-view__download-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.classify-view__download-card-head {
  display: flex;
  flex-direction: column;
  gap: 2px;

  strong {
    font-size: var(--text-sm);
  }
}

.classify-view__download-tier {
  font-size: 10.5px;
  font-weight: var(--weight-semibold);
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--color-accent-600);
}

.classify-view__download-size {
  font-size: 11.5px;
  color: var(--color-text-tertiary);
}

.classify-view__download-desc {
  font-size: 11.5px;
  color: var(--color-text-secondary);
  flex: 1;
}

.classify-view__download-progress {
  width: 100%;
}

.classify-view__progress {
  margin-top: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-neutral-soft);
}

.classify-view__progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  margin-bottom: var(--space-2);
}

.classify-view__progress-pct {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: var(--text-xs);
  color: var(--color-accent-600);
  white-space: nowrap;
}

.classify-view__progress-bar {
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-border);
  overflow: hidden;
}

.classify-view__progress-fill {
  height: 100%;
  background: var(--color-accent-500);
  border-radius: var(--radius-full);
  transition: width var(--duration-base) var(--ease-out);
}

.classify-view__progress-bar--indeterminate {
  position: relative;
}

.classify-view__progress-fill--sweep {
  position: absolute;
  width: 35%;
  animation: progress-sweep 1.3s var(--ease-in-out) infinite;
}

@keyframes progress-sweep {
  0% {
    left: -35%;
  }
  100% {
    left: 100%;
  }
}

.classify-view__progress-detail {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.classify-view__table {
  width: 100%;
  font-size: var(--text-sm);

  th {
    text-align: left;
    padding: var(--space-2) var(--space-3);
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
  }
  td {
    padding: var(--space-2) var(--space-3);
    border-top: 1px solid var(--color-border);
  }
}

.mono {
  font-family: var(--font-mono);
  font-size: 12.5px;
}

.classify-view__similar {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--text-sm);

  li {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  code {
    font-family: var(--font-mono);
    font-size: 12.5px;
  }
}

.classify-view__next {
  display: flex;
  justify-content: flex-end;
}
</style>
