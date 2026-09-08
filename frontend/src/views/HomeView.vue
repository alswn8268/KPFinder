<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { generateSampleData } from '@/api/sampleData'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import EnvCheckPanel from '@/components/env/EnvCheckPanel.vue'
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

if (!template.active) template.loadDefault()
classification.loadDefaultModel()

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
    const result = await generateSampleData(undefined, force)
    if (result.already_existed) {
      sampleAlreadyExists.value = true
      folderPath.value = result.output_dir
      ui.pushToast('이미 샘플 폴더가 있습니다. 다시 만들려면 아래 버튼을 눌러 덮어쓰세요.', 'warning')
      return
    }
    sampleAlreadyExists.value = false
    folderPath.value = result.output_dir
    ui.pushToast(`시연용 샘플 폴더를 만들었습니다 (${result.created_count}개 파일).`, 'success')
  } finally {
    generatingSample.value = false
  }
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

    <div class="home__grid">
      <BaseCard class="home__scan-card">
        <template #header>1️⃣ 정리할 폴더 선택</template>
        <div class="home__field">
          <label for="folder-path">폴더 경로</label>
          <input
            id="folder-path"
            v-model="folderPath"
            type="text"
            placeholder="예: C:\Users\me\Documents\업무폴더"
            @keyup.enter="onScan"
          />
        </div>

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

        <BaseButton block :loading="scan.scanning" @click="onScan">1️⃣ 스캔 시작</BaseButton>

        <p class="home__template-summary">
          조직 템플릿: <strong>{{ template.active?.name ?? '기본 조직 템플릿' }}</strong>
          <RouterLink to="/templates">변경</RouterLink>
        </p>
      </BaseCard>

      <div class="home__side">
        <BaseCard>
          <template #header>🧪 시연용 샘플 데이터</template>
          <p class="home__sample-desc">
            이름 규칙이 제각각인 문서 30여 개와 완전 중복 파일 4개를 포함한 어질러진 폴더를
            한 번에 만듭니다. 이미 있는 폴더는 덮어쓰지 않습니다.
          </p>
          <BaseButton variant="secondary" block :loading="generatingSample" @click="onGenerateSample(false)">
            샘플 데이터 만들기
          </BaseButton>
          <Transition name="rise">
            <div v-if="sampleAlreadyExists" class="home__sample-overwrite">
              <p>이미 폴더가 있어 새로 만들지 않았습니다.</p>
              <BaseButton variant="danger" size="sm" :loading="generatingSample" @click="onGenerateSample(true)">
                덮어쓰고 다시 만들기
              </BaseButton>
            </div>
          </Transition>
        </BaseCard>

        <BaseCard>
          <template #header>🩺 실행 환경</template>
          <EnvCheckPanel />
        </BaseCard>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.home {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.home__hero {
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

.home__grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: var(--space-6);
  align-items: start;
}

.home__side {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.home__sample-desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-4);
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

@media (max-width: 860px) {
  .home__grid {
    grid-template-columns: 1fr;
  }
}
</style>
