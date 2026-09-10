<script setup lang="ts">
import BaseButton from '@/components/base/BaseButton.vue'
import EmptyState from '@/components/base/EmptyState.vue'
</script>

<template>
  <EmptyState title="페이지를 찾을 수 없습니다." icon="🤔">
    <template #action>
      <RouterLink to="/"><BaseButton variant="secondary">시작 화면으로</BaseButton></RouterLink>
    </template>
  </EmptyState>
</template>
