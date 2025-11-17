<template>
  <div
    class="bg-[#2d2d30] border-b border-[#3e3e42] px-4 py-2 flex items-center justify-between"
  >
    <div class="flex items-center gap-4">
      <button class="text-gray-400 hover:text-gray-100 transition-colors">
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
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>
      <span class="text-sm text-gray-300">Editor de Scripts Lua</span>
    </div>
    <div class="flex items-center gap-2">
      <button
        :disabled="isExecuting"
        class="px-3 py-1.5 bg-[#0e639c] hover:bg-[#1177bb] disabled:opacity-50 disabled:cursor-not-allowed text-sm rounded flex items-center gap-2 transition-colors"
        @click="$emit('execute')"
      >
        <svg
          v-if="isExecuting"
          class="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <svg
          v-else
          class="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        {{ isExecuting ? "Executando..." : "Executar" }}
      </button>
      <button
        class="px-3 py-1.5 bg-[#3c3c3c] hover:bg-[#4a4a4a] text-sm rounded transition-colors"
        @click="$emit('clear-editor')"
      >
        Limpar
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  isExecuting: boolean;
  luaScript: string;
}

defineProps<Props>();

defineEmits<{
  execute: [];
  "load-example": [];
  "clear-editor": [];
}>();
</script>
