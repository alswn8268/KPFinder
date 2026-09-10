<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { onMounted, ref, watch } from 'vue'

import EnvDetailModal from '@/components/env/EnvDetailModal.vue'
import EnvSummaryStrip from '@/components/env/EnvSummaryStrip.vue'
import SideNav from '@/components/layout/SideNav.vue'
import StepIndicator from '@/components/layout/StepIndicator.vue'
import ToastHost from '@/components/base/ToastHost.vue'
import UsageGuideModal from '@/components/layout/UsageGuideModal.vue'
import { useClassificationStore } from '@/stores/classification'
import { useEnvStore } from '@/stores/env'
import { useScanStore } from '@/stores/scan'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const { pointColor } = storeToRefs(ui)
const env = useEnvStore()
const scan = useScanStore()
const classification = useClassificationStore()
const showGuide = ref(false)
const showEnvDetail = ref(false)

const PRESET_COLORS = ['#5B4FE9', '#0EA5A0', '#E8515A', '#2563EB', '#D97706']

onMounted(() => {
  env.check(scan.root, classification.model)
})

// "AI 모델" 상태는 사용자가 분류 화면에서 실제로 고른 모델을 반영해야 한다 — 항상
// 기본 모델(exaone3.5:2.4b)만 확인하면, 사양이 낮아 더 작은 모델을 고른 사용자에게는
// 엉뚱한 모델의 설치 여부를 보여주게 된다. 모델이 바뀔 때마다 다시 확인한다.
watch(
  () => classification.model,
  (model) => {
    if (model) env.check(scan.root, model)
  },
)

function onColorInput(e: Event) {
  ui.setPointColor((e.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="app-shell">
    <aside class="app-shell__sidebar">
      <RouterLink to="/" class="app-shell__brand">
        <img class="app-shell__logo" src="/favicon.svg" alt="" aria-hidden="true" width="32" height="32" />
        <div>
          <p class="app-shell__title">K-PathFinder</p>
          <p class="app-shell__subtitle">AI 폴더 정리 도우미 · 로컬 문서 정리</p>
        </div>
      </RouterLink>
      <SideNav />

      <div class="app-shell__color-picker">
        <p class="app-shell__color-label">포인트 컬러</p>
        <div class="app-shell__swatches">
          <button
            v-for="c in PRESET_COLORS"
            :key="c"
            class="app-shell__swatch"
            :class="{ 'is-active': pointColor.toUpperCase() === c }"
            :style="{ background: c }"
            :aria-label="`포인트 컬러 ${c}`"
            @click="ui.setPointColor(c)"
          />
          <label class="app-shell__swatch app-shell__swatch--custom">
            <input type="color" :value="pointColor" @input="onColorInput" />
          </label>
        </div>
      </div>
    </aside>

    <div class="app-shell__main">
      <header class="app-shell__topbar">
        <StepIndicator />
        <div class="app-shell__topbar-right">
          <button class="app-shell__guide-btn" @click="showGuide = true">
            <span aria-hidden="true">❓</span> 사용 가이드
          </button>
          <button
            class="app-shell__env-trigger"
            :class="{ 'is-error': env.hasBlockingError }"
            aria-label="실행 환경 상세 보기"
            @click="showEnvDetail = true"
          >
            <EnvSummaryStrip />
            <span class="app-shell__env-trigger-hint">자세히 ›</span>
          </button>
        </div>
      </header>

      <UsageGuideModal v-model="showGuide" />
      <EnvDetailModal v-model="showEnvDetail" />

      <main class="app-shell__content">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>

    <ToastHost />
  </div>
</template>

<style scoped lang="scss">
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
}

.app-shell__sidebar {
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.app-shell__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  color: inherit;
  text-decoration: none;
  transition: background-color var(--duration-fast) var(--ease-out);

  &:hover {
    background: var(--color-neutral-soft);
  }
}

.app-shell__logo {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.app-shell__title {
  font-size: var(--text-base);
  font-weight: var(--weight-bold);
}

.app-shell__subtitle {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.app-shell__color-picker {
  margin-top: auto;
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.app-shell__color-label {
  font-size: 11px;
  font-weight: var(--weight-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--space-2);
}

.app-shell__swatches {
  display: flex;
  gap: var(--space-2);
}

.app-shell__swatch {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-out);

  &:hover {
    transform: scale(1.15);
  }

  &.is-active {
    border-color: var(--color-text-primary);
  }

  &--custom {
    position: relative;
    background: conic-gradient(red, yellow, lime, cyan, blue, magenta, red);
    overflow: hidden;

    input {
      position: absolute;
      inset: -4px;
      opacity: 0;
      cursor: pointer;
    }
  }
}

.app-shell__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-shell__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-8);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  position: sticky;
  top: 0;
  z-index: 10;
}

.app-shell__topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.app-shell__guide-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border-strong);
  transition:
    border-color var(--duration-fast) var(--ease-out),
    color var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);

  &:hover {
    border-color: var(--color-accent-400);
    color: var(--color-accent-600);
    transform: translateY(-1px);
  }

  &:active {
    transform: scale(0.96);
  }
}

.app-shell__env-trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2) var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  border: 1px solid transparent;
  transition:
    border-color var(--duration-fast) var(--ease-out),
    background-color var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);

  &:hover {
    border-color: var(--color-border-strong);
    background: var(--color-neutral-soft);
    transform: translateY(-1px);
  }

  &:active {
    transform: scale(0.98);
  }

  &.is-error {
    border-color: var(--color-warning);
  }
}

.app-shell__env-trigger-hint {
  font-size: 11px;
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.app-shell__content {
  flex: 1;
  padding: var(--space-8);
  max-width: var(--container-max);
  width: 100%;
  margin: 0 auto;
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }
  .app-shell__sidebar {
    position: static;
    height: auto;
  }
}
</style>
