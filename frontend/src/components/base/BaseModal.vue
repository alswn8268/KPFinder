<script setup lang="ts">
const props = withDefaults(defineProps<{ modelValue: boolean; title?: string }>(), { title: '' })
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="props.modelValue" class="modal-overlay" @click.self="close">
        <Transition name="rise" appear>
          <div v-if="props.modelValue" class="modal" role="dialog" aria-modal="true">
            <header v-if="title" class="modal__header">
              <h3>{{ title }}</h3>
              <button class="modal__close" aria-label="닫기" @click="close">×</button>
            </header>
            <div class="modal__body">
              <slot />
            </div>
            <footer v-if="$slots.footer" class="modal__footer">
              <slot name="footer" />
            </footer>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgb(20 22 31 / 0.45);
  backdrop-filter: blur(2px);
  display: grid;
  place-items: center;
  z-index: 900;
  padding: var(--space-5);
}

.modal {
  width: min(560px, 100%);
  max-height: 85vh;
  overflow: auto;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);

  h3 {
    font-size: var(--text-lg);
  }
}

.modal__close {
  font-size: 20px;
  color: var(--color-text-tertiary);
  &:hover {
    color: var(--color-text-primary);
  }
}

.modal__body {
  padding: var(--space-6);
}

.modal__footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>
