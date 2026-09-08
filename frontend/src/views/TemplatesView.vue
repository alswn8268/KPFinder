<script setup lang="ts">
import TemplatePanel from '@/components/template/TemplatePanel.vue'
</script>

<template>
  <div class="templates-view">
    <p class="templates-view__intro">
      AI가 매번 다른 이름의 폴더를 만들어내는 것을 막기 위한 조직 표준 폴더 체계입니다.
    </p>
    <TemplatePanel />
  </div>
</template>

<style scoped lang="scss">
.templates-view__intro {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-6);
  max-width: 70ch;
}
</style>
