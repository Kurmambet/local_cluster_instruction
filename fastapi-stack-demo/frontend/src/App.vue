<script setup lang="ts">
import AuthPanel from "./components/AuthPanel.vue";
import StatusPanel from "./components/StatusPanel.vue";
import TasksPanel from "./components/TasksPanel.vue";
import WsPanel from "./components/WsPanel.vue";
</script>

<template>
  <header>
    <h1>FastAPI + PostgreSQL + Redis + Celery + Vue</h1>
  </header>
  <main>
    <StatusPanel />
    <AuthPanel />
    <TasksPanel />
    <WsPanel />
  </main>
</template>
