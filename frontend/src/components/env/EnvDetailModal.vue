<script setup lang="ts">
import BaseModal from '@/components/base/BaseModal.vue'
import EnvCheckPanel from '@/components/env/EnvCheckPanel.vue'

defineProps<{ modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [boolean] }>()
</script>

<template>
  <BaseModal :model-value="modelValue" title="🩺 실행 환경 점검" @update:model-value="$emit('update:modelValue', $event)">
    <EnvCheckPanel />
  </BaseModal>
</template>
