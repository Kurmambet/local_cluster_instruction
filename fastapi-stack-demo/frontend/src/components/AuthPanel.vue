<script setup lang="ts">
import { reactive, ref } from "vue";

import { getMe, loginUser, registerUser } from "../api";

const TOKEN_KEY = "demo_access_token";
const form = reactive({ name: "Test", email: "test@example.com", password: "password_1" });
const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));
const output = ref("");

async function run(action: () => Promise<unknown>): Promise<void> {
  try {
    output.value = JSON.stringify(await action(), null, 2);
  } catch (e) {
    output.value = `Ошибка: ${(e as Error).message}`;
  }
}

const register = () => run(() => registerUser(form.name, form.email, form.password));

const login = () =>
  run(async () => {
    const response = await loginUser(form.email, form.password);
    token.value = response.access_token;
    localStorage.setItem(TOKEN_KEY, response.access_token);
    return response;
  });

const me = () =>
  run(async () => {
    if (!token.value) throw new Error("сначала выполните вход");
    return getMe(token.value);
  });
</script>

<template>
  <section class="card">
    <h2>Пользователь (PostgreSQL + JWT)</h2>
    <p class="hint">POST /api/users/register, /login, GET /me. Пароль: 8+ символов и цифра.</p>
    <form @submit.prevent>
      <input v-model="form.name" placeholder="Имя" />
      <input v-model="form.email" type="email" placeholder="Email" />
      <input v-model="form.password" type="password" placeholder="Пароль" />
    </form>
    <div class="row" style="margin-top: .6rem">
      <button @click="register">Регистрация</button>
      <button @click="login">Войти</button>
      <button class="secondary" @click="me">Кто я?</button>
    </div>
    <pre>{{ output }}</pre>
  </section>
</template>
