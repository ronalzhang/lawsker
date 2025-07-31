<template>
  <el-form
    ref="formRef"
    :model="model"
    :rules="rules"
    :label-width="labelWidth"
    :label-position="labelPosition"
    :inline="inline"
    :size="size"
    :disabled="disabled"
    :validate-on-rule-change="validateOnRuleChange"
    :hide-required-asterisk="hideRequiredAsterisk"
    :show-message="showMessage"
    :inline-message="inlineMessage"
    :status-icon="statusIcon"
    class="lk-form"
    @validate="handleValidate"
  >
    <slot />
  </el-form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElForm } from 'element-plus'
import type { FormInstance, FormRules, FormValidateCallback } from 'element-plus'

interface Props {
  model: Record<string, any>
  rules?: FormRules
  labelWidth?: string | number
  labelPosition?: 'left' | 'right' | 'top'
  inline?: boolean
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  validateOnRuleChange?: boolean
  hideRequiredAsterisk?: boolean
  showMessage?: boolean
  inlineMessage?: boolean
  statusIcon?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  labelWidth: '100px',
  labelPosition: 'right',
  inline: false,
  size: 'default',
  disabled: false,
  validateOnRuleChange: true,
  hideRequiredAsterisk: false,
  showMessage: true,
  inlineMessage: false,
  statusIcon: false
})

const emit = defineEmits<{
  validate: [prop: string, isValid: boolean, message: string]
}>()

const formRef = ref<FormInstance>()

const validate = (callback?: FormValidateCallback) => {
  return formRef.value?.validate(callback)
}

const validateField = (props: string | string[], callback?: FormValidateCallback) => {
  return formRef.value?.validateField(props, callback)
}

const resetFields = () => {
  formRef.value?.resetFields()
}

const scrollToField = (prop: string) => {
  formRef.value?.scrollToField(prop)
}

const clearValidate = (props?: string | string[]) => {
  formRef.value?.clearValidate(props)
}

const handleValidate = (prop: string, isValid: boolean, message: string) => {
  emit('validate', prop, isValid, message)
}

defineExpose({
  validate,
  validateField,
  resetFields,
  scrollToField,
  clearValidate
})
</script>

<style scoped lang="scss">
.lk-form {
  .el-form-item {
    margin-bottom: 22px;
  }

  .el-form-item__label {
    color: var(--el-text-color-regular);
    font-weight: 500;
  }

  .el-form-item__error {
    color: var(--el-color-danger);
    font-size: 12px;
    line-height: 1;
    padding-top: 4px;
    position: absolute;
    top: 100%;
    left: 0;
  }

  // 内联表单样式
  &.el-form--inline {
    .el-form-item {
      display: inline-block;
      margin-right: 10px;
      margin-bottom: 0;
      vertical-align: top;
    }
  }

  // 标签在顶部的样式
  &.el-form--label-top {
    .el-form-item__label {
      float: none;
      display: inline-block;
      text-align: left;
      padding: 0 0 10px 0;
    }
  }
}
</style>