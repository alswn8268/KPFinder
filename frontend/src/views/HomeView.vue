<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { generateSampleData, listSampleDatasets } from '@/api/sampleData'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import type { SampleDatasetInfo } from '@/api/types'
import { useScanStore } from '@/stores/scan'
import { useTemplateStore } from '@/stores/template'
import { useUiStore } from '@/stores/ui'
import { useClassificationStore } from '@/stores/classification'

const router = useRouter()
const scan = useScanStore()
const template = useTemplateStore()
const ui = useUiStore()
const classification = useClassificationStore()

const folderPath = ref(scan.root)
const excludeDirsText = ref('')
const excludeExtsText = ref('')
const showAdvanced = ref(false)
const generatingSample = ref(false)
const sampleAlreadyExists = ref(false)
const sampleDatasets = ref<SampleDatasetInfo[]>([])
const selectedDataset = ref('general_office')
const justGenerated = ref(false)

const selectedDatasetInfo = computed(() => sampleDatasets.value.find((d) => d.key === selectedDataset.value))

if (!template.active) template.loadDefault()
classification.loadDefaultModel()
listSampleDatasets()
  .then((list) => {
    sampleDatasets.value = list
  })
  .catch(() => {
    // 목록을 못 불러와도 기본값(general_office)으로 계속 진행 가능
  })

async function onScan() {
  if (!folderPath.value.trim()) {
    ui.pushToast('정리할 폴더 경로를 입력하세요.', 'warning')
    return
  }
  scan.options.exclude_dirs = excludeDirsText.value.split(',').map((s) => s.trim()).filter(Boolean)
  scan.options.exclude_exts = excludeExtsText.value.split(',').map((s) => s.trim()).filter(Boolean)
  try {
    const result = await scan.scan(folderPath.value.trim())
    ui.pushToast(`${result.total_files}개 파일을 찾았습니다.`, 'success')
    router.push({ name: 'scan' })
  } catch {
    // 에러 토스트는 api 클라이언트 인터셉터가 이미 띄운다
  }
}

async function onGenerateSample(force = false) {
  generatingSample.value = true
  try {
    const result = await generateSampleData(undefined, force, selectedDataset.value)
    if (result.already_existed) {
      sampleAlreadyExists.value = true
      folderPath.value = result.output_dir
      ui.pushToast('이미 샘플 폴더가 있습니다. 다시 만들려면 아래 버튼을 눌러 덮어쓰세요.', 'warning')
      return
    }
    sampleAlreadyExists.value = false
    folderPath.value = result.output_dir
    ui.pushToast(`'${result.label}' 시연용 샘플 폴더를 만들었습니다 (${result.created_count}개 파일).`, 'success')
    playConfetti()
  } finally {
    generatingSample.value = false
  }
}

function playConfetti() {
  justGenerated.value = false
  requestAnimationFrame(() => {
    justGenerated.value = true
    window.setTimeout(() => {
      justGenerated.value = false
    }, 700)
  })
}
</script>

<template>
  <div class="home">
    <section class="home__hero">
      <h1>업무 폴더를 안전하게 정리하세요</h1>
      <p>
        문서 내용은 이 PC에서만 처리됩니다. 사용자가 최종 승인하기 전에는 어떤 파일도
        이동하거나 삭제하지 않습니다.
      </p>
    </section>

    <BaseCard class="home__main-card">
      <template #header>1️⃣ 정리할 폴더 선택</template>

      <div class="home__field-wrap">
        <div class="home__field" :class="{ 'home__field--success': justGenerated }">
          <label for="folder-path">폴더 경로</label>
          <input
            id="folder-path"
            v-model="folderPath"
            type="text"
            placeholder="예: C:\Users\me\Documents\업무폴더"
            @keyup.enter="onScan"
          />
        </div>
        <Transition name="pop">
          <span v-if="justGenerated" class="home__field-success" aria-hidden="true">
            ✅ 준비 완료!
            <span class="home__confetti">
              <i v-for="n in 8" :key="n" :style="{ '--angle': `${n * 45}deg` }" />
            </span>
          </span>
        </Transition>
      </div>

      <Transition name="rise">
        <div v-if="!folderPath.trim() || sampleAlreadyExists" class="home__sample">
          <div class="home__sample-head">
            <span class="home__sample-icon" aria-hidden="true">🧪</span>
            <div>
              <strong>테스트할 파일이 없나요?</strong>
              <span>시연용 샘플 데이터가 있습니다! 부서를 고르고 바로 만들어보세요.</span>
            </div>
          </div>
          <div v-if="sampleDatasets.length" class="home__dataset-tabs" role="radiogroup" aria-label="시연 시나리오">
            <button
              v-for="d in sampleDatasets"
              :key="d.key"
              type="button"
              class="home__dataset-tab"
              :class="{ 'is-active': selectedDataset === d.key }"
              role="radio"
              :aria-checked="selectedDataset === d.key"
              @click="selectedDataset = d.key"
            >
              {{ d.label }}
            </button>
          </div>
          <Transition name="fade" mode="out-in">
            <p v-if="selectedDatasetInfo" :key="selectedDatasetInfo.key" class="home__dataset-desc">
              {{ selectedDatasetInfo.description }}
            </p>
          </Transition>
          <BaseButton size="sm" variant="secondary" :loading="generatingSample" @click="onGenerateSample(false)">
            샘플 데이터 만들기
          </BaseButton>
          <Transition name="rise">
            <div v-if="sampleAlreadyExists" class="home__sample-overwrite">
              <p>이미 폴더가 있어 새로 만들지 않았습니다. 그대로 스캔하거나, 덮어쓰고 다시 만드세요.</p>
              <BaseButton variant="danger" size="sm" :loading="generatingSample" @click="onGenerateSample(true)">
                덮어쓰고 다시 만들기
              </BaseButton>
            </div>
          </Transition>
        </div>
      </Transition>

      <button class="home__advanced-toggle" @click="showAdvanced = !showAdvanced">
        {{ showAdvanced ? '고급 옵션 숨기기' : '고급 옵션 (제외 폴더/확장자)' }}
      </button>
      <Transition name="rise">
        <div v-if="showAdvanced" class="home__advanced">
          <div class="home__field">
            <label>제외할 폴더 (쉼표로 구분)</label>
            <input v-model="excludeDirsText" type="text" placeholder="예: node_modules, .git" />
          </div>
          <div class="home__field">
            <label>제외할 확장자 (쉼표로 구분)</label>
            <input v-model="excludeExtsText" type="text" placeholder="예: .log, .tmp" />
          </div>
        </div>
      </Transition>

      <BaseButton block :loading="scan.scanning" @click="onScan">2️⃣ 스캔 시작</BaseButton>

      <p class="home__template-summary">
        조직 템플릿: <strong>{{ template.active?.name ?? '기본 조직 템플릿' }}</strong>
        <RouterLink to="/templates">변경</RouterLink>
      </p>
    </BaseCard>
  </div>
</template>

<style scoped lang="scss">
@keyframes home-in {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.home {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.home__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
  animation: home-in 0.55s var(--ease-out) both;

  h1 {
    font-size: var(--text-2xl);
    background: linear-gradient(90deg, var(--color-text-primary), var(--color-accent-600));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }

  p {
    margin-top: var(--space-2);
    color: var(--color-text-secondary);
    max-width: 60ch;
  }
}

.home__main-card {
  max-width: 720px;
  margin: 0 auto;
  animation: home-in 0.55s var(--ease-out) both;
  animation-delay: 0.06s;
}

.home__sample {
  position: relative;
  margin-top: var(--space-4);
  padding: var(--space-4);
  border: 1px dashed var(--color-accent-300);
  border-radius: var(--radius-md);
  background: var(--color-accent-soft);
}

.home__sample-head {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-3);

  strong {
    display: block;
    font-size: var(--text-sm);
    margin-bottom: 2px;
  }

  span {
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
  }
}

.home__sample-icon {
  font-size: 22px;
  animation: sample-bob 2.4s var(--ease-in-out) infinite;
}

@keyframes sample-bob {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-4px) rotate(-6deg);
  }
}

.home__confetti {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  pointer-events: none;

  i {
    position: absolute;
    top: 0;
    left: 0;
    width: 6px;
    height: 6px;
    margin: -3px;
    border-radius: 50%;
    background: var(--color-accent-500);
    transform: rotate(var(--angle)) translateY(0);
    animation: confetti-burst 0.65s var(--ease-out) forwards;

    &:nth-child(3n + 1) {
      background: var(--color-success);
    }
    &:nth-child(3n + 2) {
      background: var(--color-warning);
    }
  }
}

@keyframes confetti-burst {
  0% {
    transform: rotate(var(--angle)) translateY(0);
    opacity: 1;
  }
  100% {
    transform: rotate(var(--angle)) translateY(-30px);
    opacity: 0;
  }
}

.home__dataset-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.home__dataset-tab {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  background: var(--color-surface);
  transition:
    border-color var(--duration-fast) var(--ease-out),
    background var(--duration-fast) var(--ease-out),
    color var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);

  &:hover {
    transform: translateY(-1px);
    border-color: var(--color-accent-400);
  }

  &.is-active {
    border-color: var(--color-accent-500);
    background: var(--color-accent-500);
    color: var(--color-accent-contrast);
  }
}

.home__dataset-desc {
  font-size: 11.5px;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-3);
  min-height: 1.4em;
}

.home__sample-overwrite {
  margin-top: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-warning-soft);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-items: flex-start;

  p {
    font-size: var(--text-xs);
    color: var(--color-warning);
    margin: 0;
  }
}

.home__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);

  label {
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    color: var(--color-text-secondary);
  }

  input {
    padding: var(--space-3);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
    background: var(--color-bg);
    transition: border-color var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out);

    &:focus {
      outline: none;
      border-color: var(--color-accent-500);
      box-shadow: var(--shadow-accent-glow);
    }
  }
}

.home__advanced-toggle {
  font-size: var(--text-xs);
  color: var(--color-accent-600);
  margin-bottom: var(--space-3);
}

.home__advanced {
  overflow: hidden;
  margin-bottom: var(--space-2);
}

.home__template-summary {
  margin-top: var(--space-4);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  display: flex;
  gap: var(--space-2);

  a {
    color: var(--color-accent-600);
    font-weight: var(--weight-medium);
  }
}

</style>
