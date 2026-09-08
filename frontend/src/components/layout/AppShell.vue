<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'

import SideNav from '@/components/layout/SideNav.vue'
import StepIndicator from '@/components/layout/StepIndicator.vue'
import ToastHost from '@/components/base/ToastHost.vue'
import { useEnvStore } from '@/stores/env'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const { pointColor } = storeToRefs(ui)
const env = useEnvStore()

const PRESET_COLORS = ['#5B4FE9', '#0EA5A0', '#E8515A', '#2563EB', '#D97706']

onMounted(() => {
  env.check()
})

function onColorInput(e: Event) {
  ui.setPointColor((e.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="app-shell">
    <aside class="app-shell__sidebar">
      <div class="app-shell__brand">
        <span class="app-shell__logo" aria-hidden="true">📁</span>
        <div>
          <p class="app-shell__title">AI 폴더 정리 도우미</p>
          <p class="app-shell__subtitle">로컬 문서 정리 · 안전한 이동</p>
        </div>
      </div>
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
        <div class="app-shell__env-pill" :class="{ 'is-error': env.hasBlockingError }">
          <span class="app-shell__env-dot" />
          {{ env.ollamaConnected() ? 'AI 연결됨' : 'AI 없이 사용 중' }}
        </div>
      </header>

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
}

.app-shell__logo {
  font-size: 26px;
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

.app-shell__env-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
}

.app-shell__env-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-success);
}

.app-shell__env-pill.is-error .app-shell__env-dot {
  background: var(--color-warning);
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
