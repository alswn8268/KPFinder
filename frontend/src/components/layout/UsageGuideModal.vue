<script setup lang="ts">
import BaseModal from '@/components/base/BaseModal.vue'

defineProps<{ modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [boolean] }>()

const STEPS = [
  { icon: '🩺', title: '환경 점검', body: '상단의 실행 환경 요약에서 Ollama/모델/저장공간을 자동 확인합니다. AI 관련 항목이 빨간불이어도 나머지 기능은 그대로 씁니다.' },
  { icon: '🗃️', title: '조직 템플릿 선택', body: '기본 템플릿을 쓰거나, "조직 표준 템플릿" 메뉴에서 부서별 샘플 템플릿을 골라 적용합니다.' },
  { icon: '📁', title: '폴더 스캔', body: '정리할 폴더 경로를 입력하고 스캔합니다. 테스트할 폴더가 없다면 "시연용 샘플 데이터"로 바로 만들 수 있습니다.' },
  { icon: '🤖', title: '분류 실행', body: '조직 규칙으로 먼저 분류하고, 애매한 파일만 AI로 보완합니다. 사양이 낮다면 AI 없이 규칙만으로도 계속 쓸 수 있습니다.' },
  { icon: '📝', title: '제안 편집', body: '파일별 목적지·이유·신뢰도를 확인하고 직접 수정합니다. 적용 전 최종 상태를 미리 볼 수 있습니다.' },
  { icon: '🚀', title: '적용', body: '동의 후에만 실제로 파일이 이동합니다. 중간에 실패해도 이미 옮긴 파일은 자동으로 복구됩니다.' },
  { icon: '🕘', title: '버전 관리', body: '적용마다 버전이 기록되어, 최근 버전부터 순서대로 언제든 되돌릴 수 있습니다.' },
]
</script>

<template>
  <BaseModal :model-value="modelValue" title="📖 사용 가이드" @update:model-value="$emit('update:modelValue', $event)">
    <p class="guide__intro">
      AI는 파일을 직접 옮기지 않습니다 — 항상 아래 순서로 사람이 확인·승인한 뒤에만 적용됩니다.
    </p>
    <ol class="guide__steps">
      <li v-for="(step, i) in STEPS" :key="step.title" class="guide__step" :style="{ transitionDelay: `${i * 45}ms` }">
        <span class="guide__step-icon" aria-hidden="true">{{ step.icon }}</span>
        <div>
          <p class="guide__step-title">{{ i + 1 }}. {{ step.title }}</p>
          <p class="guide__step-body">{{ step.body }}</p>
        </div>
      </li>
    </ol>
    <template #footer>
      <button class="guide__dismiss" @click="$emit('update:modelValue', false)">확인했어요</button>
    </template>
  </BaseModal>
</template>

<style scoped lang="scss">
.guide__intro {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  background: var(--color-accent-soft);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-5);
}

.guide__steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.guide__step {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-neutral-soft);
  opacity: 0;
  animation: guide-step-in 0.4s var(--ease-out) forwards;
  animation-delay: inherit;

  transition: transform var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out);

  &:hover {
    transform: translateX(3px);
    box-shadow: var(--shadow-xs);
  }
}

@keyframes guide-step-in {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.guide__step-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.guide__step-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  margin-bottom: 2px;
}

.guide__step-body {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.guide__dismiss {
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-md);
  background: var(--color-accent-500);
  color: var(--color-accent-contrast);
  font-weight: var(--weight-semibold);
  font-size: var(--text-sm);
  transition: background-color var(--duration-fast) var(--ease-out);

  &:hover {
    background: var(--color-accent-600);
  }
}
</style>
