<script setup lang="ts">
import { ref } from 'vue'

import BaseModal from '@/components/base/BaseModal.vue'

defineProps<{ modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [boolean] }>()

const STEPS = [
  {
    icon: '🩺',
    title: '환경 점검',
    summary: '상단의 실행 환경 요약에서 Ollama/모델/저장공간을 자동 확인합니다.',
    detail: [
      '상단바의 "실행 환경" 표시를 클릭하면 Python 실행 환경, 필수 라이브러리, Ollama 연결 여부, AI 모델 설치 여부, 대상 폴더 읽기/쓰기 권한, 캐시 저장 위치, 여유 저장 공간, 운영체제까지 한 번에 확인할 수 있습니다.',
      '"Ollama 실행 여부"나 "AI 모델 설치 여부"가 빨간불이어도 괜찮습니다 — 스캔, 규칙 기반 분류, 이름 변경, 버전 관리 등 핵심 기능은 AI 없이도 그대로 동작합니다.',
      '설치를 방금 마쳤거나 문제를 고쳤다면 상세 화면의 "다시 확인" 버튼으로 즉시 재점검할 수 있습니다.',
    ],
  },
  {
    icon: '🗃️',
    title: '조직 템플릿 선택',
    summary: '기본 템플릿을 쓰거나, "조직 표준 템플릿" 메뉴에서 부서별 샘플 템플릿을 골라 적용합니다.',
    detail: [
      '좌측 "조직 표준 템플릿" 메뉴에서 개발팀/운영팀/회계팀 샘플 템플릿 카드를 클릭 한 번으로 적용할 수 있습니다.',
      '"폴더 목록 직접 입력"에서 원하는 폴더 구조를 한 줄에 하나씩 입력해 나만의 템플릿을 만들 수 있습니다(작성 방법과 예시가 함께 안내됩니다).',
      '이미 정리돼 있는 폴더가 있다면 "현재 폴더 구조로 템플릿 만들기"로 그 체계를 그대로 재사용할 수 있습니다.',
      '조직 표준 템플릿은 AI가 임의로 새 폴더를 만들어내는 것도 막아줍니다 — 템플릿에 없는 폴더는 제안 자체가 걸러집니다.',
    ],
  },
  {
    icon: '📁',
    title: '폴더 스캔',
    summary: '정리할 폴더 경로를 입력하고 스캔합니다. 테스트할 폴더가 없다면 샘플 데이터로 바로 만들 수 있습니다.',
    detail: [
      '홈 화면에서 폴더 경로를 입력하고 "스캔 시작"을 누르면 파일 목록, 완전 중복 파일, 확장자별 통계를 바로 확인할 수 있습니다.',
      '경로를 비워두면 "테스트할 파일이 없나요?" 카드가 나타나, 부서별(일반 사무팀/개발팀/운영팀/회계팀) 시연용 샘플 폴더를 즉시 만들 수 있습니다.',
      '"고급 옵션"에서 제외할 폴더(예: node_modules)나 확장자(예: .log)를 지정할 수 있습니다.',
      '스캔은 읽기 전용입니다 — 이 단계에서는 어떤 파일도 이동·수정되지 않습니다.',
    ],
  },
  {
    icon: '🤖',
    title: '분류 실행',
    summary: '조직 규칙으로 먼저 분류하고, 애매한 파일만 AI로 보완합니다. 사양이 낮다면 AI 없이도 계속 쓸 수 있습니다.',
    detail: [
      '파일명이나 내용이 규칙에 걸리면 AI 호출 없이 즉시 분류됩니다(신뢰도 "높음").',
      '규칙에 걸리지 않은 파일만 요약한 뒤 AI에게 폴더 구조를 제안받습니다 — 그래서 규칙에 잘 걸리는 폴더일수록 훨씬 빠르게 끝납니다.',
      '"AI 분류 사용" 체크를 끄면 AI를 아예 호출하지 않고 규칙만으로 분류합니다. 사양이 낮은 PC에는 이 방법을 권장합니다.',
      'Ollama 모델 드롭다운에서 이 PC에 설치된 모델을 용량이 작은 순서로 고를 수 있습니다 — 작을수록 더 가볍고 빠릅니다.',
      '진행 중에는 몇 개 파일을 요약하고 있는지, AI가 폴더 구조를 제안하는 데 시간이 얼마나 걸리는지 실시간으로 표시됩니다.',
    ],
  },
  {
    icon: '📝',
    title: '제안 편집',
    summary: '파일별 목적지·이유·신뢰도를 확인하고 직접 수정합니다. 적용 전 최종 상태를 미리 볼 수 있습니다.',
    detail: [
      '파일마다 추천 폴더, 추천 이유, 신뢰도(높음/보통/낮음), 출처(규칙/AI/사용자)를 표로 확인할 수 있습니다.',
      '목적지를 직접 입력해 바꾸거나, 여러 파일을 한 번에 골라 다른 폴더로 옮길 수 있습니다.',
      '마음에 안 드는 파일은 "제외" 체크로 이번 적용에서 빼고 나중에 따로 처리할 수 있습니다.',
      '하단 "최종 상태" 표에서 실제로 적용했을 때 이동/유지/제외/충돌될 파일을 미리 확인할 수 있습니다.',
      'JSON·엑셀·HTML 리포트를 내려받아 정리 결과를 기록으로 남길 수 있습니다.',
    ],
  },
  {
    icon: '🚀',
    title: '적용',
    summary: '동의 후에만 실제로 파일이 이동합니다. 중간에 실패해도 이미 옮긴 파일은 자동으로 복구됩니다.',
    detail: [
      '최종 이동 계획을 다시 한 번 확인하고, 동의 체크박스를 눌러야만 "적용" 버튼이 활성화됩니다.',
      '이동 계획은 시작 전에 먼저 저장되고, 파일마다 즉시 로그가 남습니다.',
      '도중에 오류가 나면 이미 옮긴 파일까지 전부 자동으로 원래 위치로 되돌립니다.',
      '목적지가 대상 폴더를 벗어나거나, 예약어·금지 문자를 포함하거나, 기존 파일과 이름이 충돌하면 그 파일만 자동으로 걸러지고 사유가 함께 표시됩니다.',
    ],
  },
  {
    icon: '🕘',
    title: '버전 관리',
    summary: '적용마다 버전이 기록되어, 최근 버전부터 순서대로 언제든 되돌릴 수 있습니다.',
    detail: [
      '"적용"할 때마다 새 버전으로 기록되며, 몇 개 파일이 옮겨졌는지도 함께 남습니다.',
      '되돌리기는 항상 가장 최근 버전부터 순서대로만 할 수 있습니다 — 중간 버전을 건너뛰면 파일 위치가 꼬일 수 있기 때문입니다.',
      '실제로 옮긴 파일이 0개인 적용은 버전으로 남지 않습니다 — 되돌릴 것도 없는 빈 기록이 "최근 버전" 자리를 차지해 진짜 버전을 되돌리지 못하게 막는 일이 없도록 한 것입니다.',
      '되돌린 뒤에 다시 적용해도 새 버전으로 기록되니, 안심하고 여러 번 시도해볼 수 있습니다.',
    ],
  },
]

const openIndex = ref<number | null>(null)

function toggle(i: number) {
  openIndex.value = openIndex.value === i ? null : i
}
</script>

<template>
  <BaseModal :model-value="modelValue" title="📖 사용 가이드" @update:model-value="$emit('update:modelValue', $event)">
    <p class="guide__intro">
      AI는 파일을 직접 옮기지 않습니다 — 항상 아래 순서로 사람이 확인·승인한 뒤에만 적용됩니다.
      번호를 클릭하면 더 자세한 내용을 볼 수 있습니다.
    </p>
    <ol class="guide__steps">
      <li
        v-for="(step, i) in STEPS"
        :key="step.title"
        class="guide__step"
        :class="{ 'is-open': openIndex === i }"
        :style="{ transitionDelay: `${i * 45}ms` }"
      >
        <button type="button" class="guide__step-header" :aria-expanded="openIndex === i" @click="toggle(i)">
          <span class="guide__step-icon" aria-hidden="true">{{ step.icon }}</span>
          <div class="guide__step-heading">
            <p class="guide__step-title">{{ i + 1 }}. {{ step.title }}</p>
            <p class="guide__step-summary">{{ step.summary }}</p>
          </div>
          <span class="guide__step-chevron" aria-hidden="true">›</span>
        </button>
        <div class="guide__step-collapse">
          <ul class="guide__step-detail">
            <li v-for="(line, j) in step.detail" :key="j">{{ line }}</li>
          </ul>
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
  border-radius: var(--radius-md);
  background: var(--color-neutral-soft);
  opacity: 0;
  animation: guide-step-in 0.4s var(--ease-out) forwards;
  animation-delay: inherit;
  overflow: hidden;
  transition: box-shadow var(--duration-fast) var(--ease-out);

  &.is-open {
    box-shadow: var(--shadow-xs);
    background: var(--color-surface);
    border: 1px solid var(--color-accent-200);
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

.guide__step-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3);
  text-align: left;
  cursor: pointer;
}

.guide__step-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.guide__step-heading {
  flex: 1;
  min-width: 0;
}

.guide__step-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  margin-bottom: 2px;
}

.guide__step-summary {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.guide__step-chevron {
  flex-shrink: 0;
  font-size: 18px;
  color: var(--color-text-tertiary);
  transform: rotate(90deg);
  transition: transform var(--duration-fast) var(--ease-out);
  line-height: 1;
  margin-top: 2px;
}

.guide__step.is-open .guide__step-chevron {
  transform: rotate(-90deg);
  color: var(--color-accent-600);
}

.guide__step-collapse {
  max-height: 0;
  overflow: hidden;
  transition: max-height var(--duration-base) var(--ease-out);
}

.guide__step.is-open .guide__step-collapse {
  max-height: 400px;
}

.guide__step-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: 0;
  padding: 0 var(--space-3) var(--space-3) 48px;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  list-style: disc;
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
