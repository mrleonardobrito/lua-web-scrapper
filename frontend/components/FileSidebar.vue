<template>
  <div class="w-64 bg-[#252526] border-r border-[#3e3e42] flex flex-col">
    <div class="px-3 py-2 border-b border-[#3e3e42]">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-semibold text-gray-300">Files</h2>
        <input
          type="text"
          placeholder="Search..."
          class="w-32 px-2 py-1 text-xs bg-[#3c3c3c] border border-[#3e3e42] rounded text-gray-300 placeholder-gray-500 focus:outline-none focus:border-[#0e639c]"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-2">
      <div class="mb-4">
        <h3 class="text-xs font-medium text-gray-400 mb-2 px-2">Exemplos</h3>
        <div class="space-y-1">
          <button
            v-for="example in examples"
            :key="example.id"
            class="w-full text-left px-2 py-1.5 rounded text-xs text-gray-300 hover:bg-[#2a2d2e] transition-colors flex items-center gap-2"
            @click="$emit('load-example', String(example.id))"
          >
            <svg
              class="w-3 h-3 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            {{ example.name }}
          </button>
        </div>
      </div>

      <div v-if="isAuthenticated">
        <div class="flex items-center justify-between mb-2 px-2">
          <h3 class="text-xs font-medium text-gray-400">Meus Scripts</h3>
          <button
            class="text-gray-500 hover:text-gray-300 transition-colors"
            title="Novo script"
            @click="$emit('create-new-script')"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
          </button>
        </div>

        <div v-if="scriptsLoading" class="text-center py-4">
          <div
            class="animate-spin rounded-full h-5 w-5 border-b-2 border-[#0e639c] mx-auto"
          />
        </div>

        <div
          v-else-if="userScripts.length === 0"
          class="text-center py-4 text-gray-500 text-xs px-2"
        >
          Nenhum script salvo
        </div>

        <div v-else class="space-y-1">
          <button
            v-for="script in userScripts"
            :key="script.id"
            :class="[
              'w-full text-left px-2 py-1.5 rounded text-xs transition-colors flex items-center gap-2',
              currentScriptId === script.id
                ? 'bg-[#094771] text-gray-100'
                : 'text-gray-300 hover:bg-[#2a2d2e]',
            ]"
            @click="$emit('load-script', script.id)"
          >
            <svg
              class="w-3 h-3 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">
                {{ script.name }}
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Mensagem para usuários não autenticados -->
      <div v-else class="text-center py-4 px-2">
        <p class="text-xs text-gray-500 mb-3">
          Faça login para salvar e gerenciar seus scripts
        </p>
        <button
          class="bg-[#0e639c] text-white px-3 py-1.5 rounded text-xs hover:bg-[#1177bb] transition-colors"
          @click="$emit('login')"
        >
          Entrar
        </button>
      </div>
    </div>

    <!-- User Profile no canto inferior -->
    <div
      v-if="isAuthenticated && user"
      class="border-t border-[#3e3e42] p-3 mt-auto"
    >
      <div class="flex items-center gap-3">
        <!-- Avatar -->
        <div
          class="w-10 h-10 rounded-full bg-[#ff6b9d] flex items-center justify-center flex-shrink-0"
        >
          <span class="text-white font-semibold text-sm">
            {{ getUserInitial(user) }}
          </span>
        </div>
        <!-- Nome -->
        <div class="flex-1 min-w-0">
          <div class="text-sm text-gray-100 font-medium truncate">
            {{ getUserDisplayName(user) }}
          </div>
        </div>
        <!-- Botão de Logout -->
        <button
          class="text-gray-400 hover:text-red-400 transition-colors p-1 rounded hover:bg-[#3c3c3c]"
          title="Sair"
          @click="$emit('logout')"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { User } from "../composables/useAuth";
import type { Script } from "../composables/useLuaScripts";

interface Props {
  isAuthenticated: boolean;
  user: User | null;
  examples: Script[];
  userScripts: Script[];
  scriptsLoading: boolean;
  currentScriptId?: number | null;
}

withDefaults(defineProps<Props>(), {
  currentScriptId: null,
});

defineEmits<{
  "load-example": [exampleId: string];
  "load-script": [scriptId: number];
  "create-new-script": [];
  login: [];
  logout: [];
}>();

const formatExecutionDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const formatExecutionStatus = (status: string): string => {
  const statusMap = {
    pending: "Pendente",
    running: "Executando",
    success: "Sucesso",
    error: "Erro",
  };
  return statusMap[status] || status;
};

const getUserInitial = (user: User): string => {
  if (user.first_name) {
    return user.first_name.charAt(0).toUpperCase();
  }
  if (user.username) {
    return user.username.charAt(0).toUpperCase();
  }
  return "U";
};

const getUserDisplayName = (user: User): string => {
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`;
  }
  if (user.first_name) {
    return user.first_name;
  }
  return user.username || "Usuário";
};
</script>
