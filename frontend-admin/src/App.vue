<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onMounted(() => {
  // 初始化用户状态
  userStore.checkLoginStatus()
})
</script>

<style lang="scss">
#app {
  height: 100vh;
  overflow: hidden;
}
</style>