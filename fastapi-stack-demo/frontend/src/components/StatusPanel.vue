<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getStatus, type ReadinessResponse } from "../api";

const status = ref<ReadinessResponse | null>(null);
const error = ref("");

async function refresh(): Promise<void> {
  error.value = "";
  try {
    status.value = await getStatus();
  } catch (e) {
    status.value = null;
    error.value = (e as Error).message;
  }
}

onMounted(refresh);
</script>

<template>
  <section class="card">
    <h2>Статус (readiness)</h2>
    <p class="hint">GET /api/status — то же, что /readyz: проверка PostgreSQL и Redis</p>
    <div class="row">
      <button @click="refresh">Обновить</button>
      <span v-if="status" :class="status.ready ? 'ok' : 'bad'">
        {{ status.ready ? "готов" : "не готов" }}
      </span>
    </div>
    <pre>{{ error || JSON.stringify(status, null, 2) }}</pre>
  </section>
</template>
