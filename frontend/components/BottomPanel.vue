<template>
  <div
    v-if="executionResult"
    class="h-48 bg-[#1e1e1e] border-t border-[#3e3e42] flex flex-col"
  >
    <div class="px-3 py-2 border-b border-[#3e3e42] flex items-center gap-2">
      <button
        :class="[
          'px-2 py-1 text-xs rounded transition-colors',
          activeTab === 'output'
            ? 'bg-[#094771] text-gray-100'
            : 'text-gray-400 hover:text-gray-200',
        ]"
        @click="activeTab = 'output'"
      >
        Output
      </button>
      <button
        :class="[
          'px-2 py-1 text-xs rounded transition-colors',
          activeTab === 'terminal'
            ? 'bg-[#094771] text-gray-100'
            : 'text-gray-400 hover:text-gray-200',
        ]"
        @click="activeTab = 'terminal'"
      >
        Terminal
      </button>
    </div>
    <div class="flex-1 overflow-y-auto p-3">
      <div
        v-if="activeTab === 'output'"
        class="text-xs font-mono text-gray-300"
      >
        <div v-if="executionResult.script_executed" class="text-green-400">
          ✓ Script executado com sucesso
        </div>
        <div v-else class="text-red-400">✗ Erro na execução</div>
        <div v-if="executionResult.error" class="mt-2 text-red-400">
          {{ executionResult.error }}
        </div>
      </div>
      <div v-else class="text-xs font-mono text-gray-400">
        Terminal não disponível
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

interface ExecutionResult {
  script_executed: boolean;
  error?: string;
}

interface Props {
  executionResult: ExecutionResult | null;
}

defineProps<Props>();

const activeTab = ref<"output" | "terminal">("output");
</script>
