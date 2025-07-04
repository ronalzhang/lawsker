<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// Lawsker (律思客) - 主应用组件
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  console.log('🚀 Lawsker (律思客) 应用启动成功')
  console.log('法律智慧，即刻送达')
})
</script>

<style lang="scss">
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  width: 100vw;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  overflow-x: hidden;
}

.el-button {
  font-weight: 500;
}

.el-menu {
  border-right: none !important;
}
</style> 