<template>
  <button
    :class="buttonClass"
    :disabled="disabled || loading"
    :type="htmlType"
    @click="handleClick"
  >
    <el-icon v-if="loading" class="is-loading">
      <Loading />
    </el-icon>
    <el-icon v-else-if="icon">
      <component :is="icon" />
    </el-icon>
    <span v-if="$slots.default">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElIcon } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

interface Props {
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text'
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  loading?: boolean
  icon?: any
  round?: boolean
  circle?: boolean
  plain?: boolean
  htmlType?: 'button' | 'submit' | 'reset'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'default',
  size: 'default',
  disabled: false,
  loading: false,
  round: false,
  circle: false,
  plain: false,
  htmlType: 'button'
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonClass = computed(() => {
  return [
    'lk-button',
    `lk-button--${props.type}`,
    `lk-button--${props.size}`,
    {
      'is-disabled': props.disabled,
      'is-loading': props.loading,
      'is-round': props.round,
      'is-circle': props.circle,
      'is-plain': props.plain
    }
  ]
})

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>

<style scoped lang="scss">
.lk-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  height: 32px;
  white-space: nowrap;
  cursor: pointer;
  color: var(--el-text-color-regular);
  text-align: center;
  box-sizing: border-box;
  outline: none;
  transition: 0.1s;
  font-weight: 500;
  user-select: none;
  vertical-align: middle;
  -webkit-appearance: none;
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  padding: 8px 15px;
  font-size: 14px;

  &:hover,
  &:focus {
    color: var(--el-color-primary);
    border-color: var(--el-color-primary-light-7);
    background-color: var(--el-color-primary-light-9);
  }

  &:active {
    color: var(--el-color-primary-dark-2);
    border-color: var(--el-color-primary-dark-2);
    outline: none;
  }

  &.is-disabled {
    color: var(--el-text-color-placeholder);
    cursor: not-allowed;
    background-image: none;
    background-color: var(--el-bg-color);
    border-color: var(--el-border-color-light);

    &:hover,
    &:focus {
      color: var(--el-text-color-placeholder);
      background-color: var(--el-bg-color);
      border-color: var(--el-border-color-light);
    }
  }

  &.is-loading {
    position: relative;
    pointer-events: none;

    &:before {
      pointer-events: none;
      content: '';
      position: absolute;
      left: -1px;
      top: -1px;
      right: -1px;
      bottom: -1px;
      border-radius: inherit;
      background-color: var(--el-mask-color-extra-light);
    }
  }

  &.is-round {
    border-radius: 20px;
    padding: 8px 15px;
  }

  &.is-circle {
    border-radius: 50%;
    padding: 8px;
    width: 32px;
  }

  // 类型样式
  &--primary {
    color: #fff;
    background-color: var(--el-color-primary);
    border-color: var(--el-color-primary);

    &:hover,
    &:focus {
      background-color: var(--el-color-primary-light-3);
      border-color: var(--el-color-primary-light-3);
      color: #fff;
    }

    &:active {
      background-color: var(--el-color-primary-dark-2);
      border-color: var(--el-color-primary-dark-2);
      color: #fff;
    }

    &.is-plain {
      color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
      border-color: var(--el-color-primary-light-5);

      &:hover,
      &:focus {
        background: var(--el-color-primary);
        border-color: var(--el-color-primary);
        color: #fff;
      }
    }
  }

  &--success {
    color: #fff;
    background-color: var(--el-color-success);
    border-color: var(--el-color-success);

    &:hover,
    &:focus {
      background-color: var(--el-color-success-light-3);
      border-color: var(--el-color-success-light-3);
      color: #fff;
    }
  }

  &--warning {
    color: #fff;
    background-color: var(--el-color-warning);
    border-color: var(--el-color-warning);

    &:hover,
    &:focus {
      background-color: var(--el-color-warning-light-3);
      border-color: var(--el-color-warning-light-3);
      color: #fff;
    }
  }

  &--danger {
    color: #fff;
    background-color: var(--el-color-danger);
    border-color: var(--el-color-danger);

    &:hover,
    &:focus {
      background-color: var(--el-color-danger-light-3);
      border-color: var(--el-color-danger-light-3);
      color: #fff;
    }
  }

  &--info {
    color: #fff;
    background-color: var(--el-color-info);
    border-color: var(--el-color-info);

    &:hover,
    &:focus {
      background-color: var(--el-color-info-light-3);
      border-color: var(--el-color-info-light-3);
      color: #fff;
    }
  }

  &--text {
    border-color: transparent;
    color: var(--el-color-primary);
    background: transparent;
    padding-left: 0;
    padding-right: 0;

    &:hover,
    &:focus {
      color: var(--el-color-primary-light-3);
      border-color: transparent;
      background-color: transparent;
    }
  }

  // 尺寸样式
  &--large {
    height: 40px;
    padding: 12px 19px;
    font-size: 14px;
    border-radius: var(--el-border-radius-base);

    &.is-circle {
      width: 40px;
      padding: 12px;
    }
  }

  &--small {
    height: 24px;
    padding: 5px 11px;
    font-size: 12px;
    border-radius: calc(var(--el-border-radius-base) - 1px);

    &.is-circle {
      width: 24px;
      padding: 5px;
    }
  }

  .el-icon {
    margin-right: 6px;

    &.is-loading {
      animation: rotating 2s linear infinite;
    }
  }

  .el-icon + span {
    margin-left: 6px;
  }
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>