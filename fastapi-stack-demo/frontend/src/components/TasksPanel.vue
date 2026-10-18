<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";

import { enqueueAdd, getTask, type TaskStatus } from "../api";

const a = ref(2);
const b = ref(3);
const task = ref<TaskStatus | null>(null);
const error = ref("");
let timer: number | undefined;

function stopPolling(): void {
  if (timer !== undefined) window.clearInterval(timer);
  timer = undefined;
}

async function start(): Promise<void> {
  stopPolling();
  error.value = "";
  try {
    const created = await enqueueAdd(a.value, b.value);
    timer = window.setInterval(async () => {
      try {
        task.value = await getTask(created.task_id);
        if (task.value.state === "SUCCESS" || task.value.state === "FAILURE") stopPolling();
      } catch (e) {
        error.value = (e as Error).message;
        stopPolling();
      }
    }, 1000);
  } catch (e) {
    error.value = (e as Error).message;
  }
}

onBeforeUnmount(stopPolling);
</script>

<template>
  <section class="card">
    <h2>Фоновая задача (Celery + Redis)</h2>
    <p class="hint">POST /api/tasks/add ставит задачу в очередь, воркер «считает» 3 секунды</p>
    <div class="row">
      <input v-model.number="a" type="number" />
      <span>+</span>
      <input v-model.number="b" type="number" />
      <button @click="start">Запустить</button>
    </div>
    <pre>{{ error || JSON.stringify(task, null, 2) }}</pre>
  </section>
</template>
