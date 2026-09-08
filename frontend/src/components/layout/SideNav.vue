<script setup lang="ts">
import { computed } from 'vue'

import { useScanStore } from '@/stores/scan'
import { useClassificationStore } from '@/stores/classification'

const scan = useScanStore()
const classification = useClassificationStore()

const coreLinks = computed(() => [
  { to: '/', label: '시작', icon: '🏠', enabled: true },
  { to: '/scan', label: '스캔 결과', icon: '📋', enabled: scan.hasScanned },
  { to: '/classify', label: '분류 실행', icon: '🤖', enabled: scan.hasScanned },
  { to: '/proposal', label: '제안 편집', icon: '📝', enabled: classification.hasResult },
  { to: '/apply', label: '적용', icon: '🚀', enabled: classification.hasResult },
  { to: '/versions', label: '버전 관리', icon: '🕘', enabled: !!scan.root },
])

const toolLinks = computed(() => [
  { to: '/directory-graph', label: '디렉토리 구조/연관도', icon: '🗂️', enabled: scan.hasScanned },
  { to: '/content-graph', label: '파일 연관도', icon: '🕸️', enabled: scan.hasScanned },
  { to: '/rename', label: '이름 일괄 변경', icon: '✂️', enabled: scan.hasScanned },
  { to: '/templates', label: '조직 표준 템플릿', icon: '🗃️', enabled: true },
])
</script>

<template>
  <nav class="side-nav">
    <p class="side-nav__group-label">핵심 흐름</p>
    <ul>
      <li v-for="link in coreLinks" :key="link.to">
        <RouterLink :to="link.to" class="side-nav__link" :class="{ 'is-disabled': !link.enabled }">
          <span class="side-nav__icon" aria-hidden="true">{{ link.icon }}</span>
          {{ link.label }}
        </RouterLink>
      </li>
    </ul>

    <p class="side-nav__group-label">도구</p>
    <ul>
      <li v-for="link in toolLinks" :key="link.to">
        <RouterLink :to="link.to" class="side-nav__link" :class="{ 'is-disabled': !link.enabled }">
          <span class="side-nav__icon" aria-hidden="true">{{ link.icon }}</span>
          {{ link.label }}
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>

<style scoped lang="scss">
.side-nav {
  padding: var(--space-2) 0;
}

.side-nav__group-label {
  padding: var(--space-4) var(--space-4) var(--space-2);
  font-size: 11px;
  font-weight: var(--weight-semibold);
  letter-spacing: 0.04em;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
}

.side-nav__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  margin: 0 var(--space-2);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  position: relative;
  transition:
    background-color var(--duration-fast) var(--ease-out),
    color var(--duration-fast) var(--ease-out);

  &:hover {
    background: var(--color-neutral-soft);
    color: var(--color-text-primary);
  }

  &.router-link-active {
    background: var(--color-accent-soft);
    color: var(--color-accent-600);

    &::before {
      content: '';
      position: absolute;
      left: -8px;
      top: 20%;
      bottom: 20%;
      width: 3px;
      border-radius: var(--radius-full);
      background: var(--color-accent-500);
    }
  }

  &.is-disabled {
    opacity: 0.45;
  }
}

.side-nav__icon {
  font-size: 15px;
  width: 18px;
  text-align: center;
}
</style>
