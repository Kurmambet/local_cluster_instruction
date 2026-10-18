<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";

import { wsUrl } from "../api";

const socket = ref<WebSocket | null>(null);
const active = ref<number | null>(null);
const message = ref("hello");
const log = ref<string[]>([]);

function push(line: string): void {
  log.value = [...log.value.slice(-9), line];
}

function connect(): void {
  if (socket.value) return;
  const ws = new WebSocket(wsUrl());
  ws.onopen = () => push("подключено");
  ws.onclose = () => {
    push("отключено");
    socket.value = null;
    active.value = null;
  };
  ws.onmessage = (event: MessageEvent<string>) => {
    const data = JSON.parse(event.data) as { type: string; active?: number; data?: string };
    if (data.type === "active") active.value = data.active ?? null;
    else push(`${data.type}${data.data ? `: ${data.data}` : ""}`);
  };
  socket.value = ws;
}

function disconnect(): void {
  socket.value?.close();
}

function send(): void {
  socket.value?.send(message.value);
}

onBeforeUnmount(disconnect);
</script>

<template>
  <section class="card">
    <h2>WebSocket (счётчик подключений)</h2>
    <p class="hint">/ws/counter — эхо, heartbeat каждые 15 с, число подключений видно в Grafana</p>
    <div class="row">
      <button :disabled="!!socket" @click="connect">Подключиться</button>
      <button class="secondary" :disabled="!socket" @click="disconnect">Отключиться</button>
      <span>активных: <b>{{ active ?? "—" }}</b></span>
    </div>
    <div class="row" style="margin-top: .6rem">
      <input v-model="message" />
      <button :disabled="!socket" @click="send">Отправить</button>
    </div>
    <pre>{{ log.join("\n") }}</pre>
  </section>
</template>
