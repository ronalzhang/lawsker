<template>
  <el-dialog
    v-model="visible"
    :title="title"
    :width="width"
    :fullscreen="fullscreen"
    :top="top"
    :modal="modal"
    :modal-class="modalClass"
    :append-to-body="appendToBody"
    :lock-scroll="lockScroll"
    :custom-class="customClass"
    :open-delay="openDelay"
    :close-delay="closeDelay"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :show-close="showClose"
    :before-close="handleBeforeClose"
    :center="center"
    :align-center="alignCenter"
    :destroy-on-close="destroyOnClose"
    class="lk-modal"
    @open="handleOpen"
    @opened="handleOpened"
    @close="handleClose"
    @closed="handleClosed"
  >
    <template #header v-if="$slots.header">
      <slot name="header" />
    </template>

    <div class="lk-modal__body">
      <slot />
    </div>

    <template #footer v-if="$slots.footer || showDefaultFooter">
      <slot name="footer">
        <div class="lk-modal__footer" v-if="showDefaultFooter">
          <lk-button @click="handleCancel">{{ cancelText }}</lk-button>
          <lk-button
            type="primary"
            :loading="confirmLoading"
            @click="handleConfirm"
          >
            {{ confirmText }}
          </lk-button>
        </div>
      </slot>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElDialog } from 'element-plus'
import LkButton from '../Button/index.vue'

interface Props {
  modelValue: boolean
  title?: string
  width?: string | number
  fullscreen?: boolean
  top?: string
  modal?: boolean
  modalClass?: string
  appendToBody?: boolean
  lockScroll?: boolean
  customClass?: string
  openDelay?: number
  closeDelay?: number
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  showClose?: boolean
  center?: boolean
  alignCenter?: boolean
  destroyOnClose?: boolean
  showDefaultFooter?: boolean
  confirmText?: string
  cancelText?: string
  confirmLoading?: boolean
  beforeClose?: (done: () => void) => void
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  width: '50%',
  fullscreen: false,
  top: '15vh',
  modal: true,
  appendToBody: false,
  lockScroll: true,
  openDelay: 0,
  closeDelay: 0,
  closeOnClickModal: true,
  closeOnPressEscape: true,
  showClose: true,
  center: false,
  alignCenter: false,
  destroyOnClose: false,
  showDefaultFooter: false,
  confirmText: '确定',
  cancelText: '取消',
  confirmLoading: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  open: []
  opened: []
  close: []
  closed: []
  confirm: []
  cancel: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

const handleBeforeClose = (done: () => void) => {
  if (props.beforeClose) {
    props.beforeClose(done)
  } else {
    done()
  }
}

const handleOpen = () => {
  emit('open')
}

const handleOpened = () => {
  emit('opened')
}

const handleClose = () => {
  emit('close')
}

const handleClosed = () => {
  emit('closed')
}

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
  visible.value = false
}
</script>

<style scoped lang="scss">
.lk-modal {
  .lk-modal__body {
    padding: 20px 0;
    color: var(--el-text-color-regular);
    font-size: 14px;
    word-break: break-all;
  }

  .lk-modal__footer {
    text-align: right;

    .lk-button + .lk-button {
      margin-left: 10px;
    }
  }

  :deep(.el-dialog__header) {
    padding: 20px 20px 10px;
    margin-right: 16px;
  }

  :deep(.el-dialog__body) {
    padding: 10px 20px;
    color: var(--el-text-color-regular);
    font-size: 14px;
  }

  :deep(.el-dialog__footer) {
    padding: 10px 20px 20px;
    text-align: right;
    box-sizing: border-box;
  }

  :deep(.el-dialog__title) {
    line-height: 24px;
    font-size: 18px;
    color: var(--el-text-color-primary);
  }

  :deep(.el-dialog__close) {
    color: var(--el-text-color-secondary);
    font-size: 16px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .lk-modal {
    :deep(.el-dialog) {
      width: 90% !important;
      margin-top: 5vh !important;
    }
  }
}
</style>