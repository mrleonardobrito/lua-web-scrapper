<template>
  <div class="w-96 bg-[#252526] border-l border-[#3e3e42] flex flex-col">
    <div class="px-3 py-2 border-b border-[#3e3e42]">
      <h2 class="text-sm font-semibold text-gray-300">Resultado</h2>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <!-- Status -->
      <div v-if="executionResult" class="mb-4">
        <div
          :class="[
            'px-3 py-2 rounded text-sm mb-3',
            executionResult.script_executed
              ? 'bg-green-900/30 text-green-400 border border-green-800'
              : 'bg-red-900/30 text-red-400 border border-red-800',
          ]"
        >
          {{
            executionResult.script_executed
              ? "Script executado com sucesso"
              : "Erro na execução"
          }}
        </div>

        <!-- Passos de execução -->
        <div v-if="executionSteps.length > 0" class="mt-4 mb-4">
          <h4 class="text-xs font-medium text-gray-400 mb-2">
            Passos Executados
          </h4>
          <div class="space-y-1">
            <div
              v-for="step in executionSteps"
              :key="step.index"
              class="flex items-center justify-between px-2 py-1.5 bg-[#2a2d2e] rounded text-xs"
            >
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-300"
                  >Passo {{ step.index }}:</span
                >
                <span class="text-gray-400">{{ step.title }}</span>
              </div>
              <span
                :class="[
                  'px-2 py-0.5 rounded text-[10px] font-medium',
                  step.status === 'success'
                    ? 'bg-green-900/30 text-green-400'
                    : step.status === 'error'
                    ? 'bg-red-900/30 text-red-400'
                    : step.status === 'running'
                    ? 'bg-blue-900/30 text-blue-400'
                    : 'bg-gray-700 text-gray-400',
                ]"
              >
                {{
                  step.status === "success"
                    ? "Sucesso"
                    : step.status === "error"
                    ? "Erro"
                    : step.status === "running"
                    ? "Executando"
                    : "Pendente"
                }}
              </span>
            </div>
          </div>
        </div>

        <!-- Dropdown de erro -->
        <div
          v-if="!executionResult.script_executed && showErrorDetails"
          class="mt-3 mb-4"
        >
          <button
            class="w-full flex items-center justify-between px-3 py-2 bg-red-900/20 border border-red-800 rounded text-sm text-red-400 hover:bg-red-900/30 transition-colors"
            @click="showErrorDetails = !showErrorDetails"
          >
            <span class="font-medium">Detalhes do Erro</span>
            <svg
              :class="[
                'w-4 h-4 transition-transform',
                showErrorDetails ? 'rotate-180' : '',
              ]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          <div
            v-if="showErrorDetails"
            class="mt-2 px-3 py-2 bg-[#2a2d2e] border border-red-800/50 rounded"
          >
            <div
              v-if="executionResult.error || executionResult.script_error"
              class="mb-2"
            >
              <p class="text-xs font-semibold text-red-400 mb-1">Mensagem:</p>
              <pre
                class="text-xs text-red-300 whitespace-pre-wrap break-words font-mono"
                >{{
                  executionResult.error || executionResult.script_error
                }}</pre
              >
            </div>
            <div v-if="executionResult.details" class="mb-2">
              <p class="text-xs font-semibold text-red-400 mb-1">Detalhes:</p>
              <pre
                class="text-xs text-red-300 whitespace-pre-wrap break-words font-mono"
                >{{ executionResult.details }}</pre
              >
            </div>
            <div v-if="executionResult.splash_response?.error">
              <p class="text-xs font-semibold text-red-400 mb-1">
                Erro do Splash:
              </p>
              <pre
                class="text-xs text-red-300 whitespace-pre-wrap break-words font-mono"
                >{{ executionResult.splash_response.error }}</pre
              >
            </div>
            <div
              v-if="
                executionResult.splash_response?.errors &&
                executionResult.splash_response.errors.length > 0
              "
            >
              <p class="text-xs font-semibold text-red-400 mb-1">Erros:</p>
              <pre
                class="text-xs text-red-300 whitespace-pre-wrap break-words font-mono"
                >{{
                  JSON.stringify(
                    executionResult.splash_response.errors,
                    null,
                    2
                  )
                }}</pre
              >
            </div>
          </div>
        </div>

        <!-- Screenshot Preview -->
        <div v-if="executionResult?.screenshot_url" class="mb-4">
          <h3 class="text-xs font-medium text-gray-400 mb-2">Screenshot</h3>
          <div
            class="relative border border-[#3e3e42] rounded overflow-hidden bg-[#1e1e1e]"
          >
            <img
              v-if="executionResult?.screenshot_url"
              :src="executionResult?.screenshot_url"
              alt="Screenshot do script"
              class="w-full h-auto cursor-pointer hover:opacity-90 transition-opacity"
              @click="
                $emit('open-screenshot-modal', executionResult?.screenshot_url)
              "
            />
            <div
              class="absolute top-2 right-2 bg-black/70 text-white text-[10px] px-2 py-1 rounded"
            >
              Clique para ampliar
            </div>
          </div>
        </div>

        <!-- Dados retornados -->
        <div v-if="executionResult?.splash_response" class="mb-4">
          <button
            class="w-full flex items-center justify-between px-3 py-2 bg-blue-900/20 border border-blue-800 rounded text-sm text-blue-400 hover:bg-blue-900/30 transition-colors"
            @click="showDataDetails = !showDataDetails"
          >
            <span class="font-medium">Dados Retornados</span>
            <svg
              :class="[
                'w-4 h-4 transition-transform',
                showDataDetails ? 'rotate-180' : '',
              ]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          <div
            v-if="showDataDetails"
            class="mt-2 px-3 py-2 bg-[#2a2d2e] border border-[#3e3e42] rounded"
          >
            <pre
              class="text-xs text-gray-300 whitespace-pre-wrap break-words overflow-auto max-h-96 font-mono"
              >{{
                JSON.stringify(executionResult.splash_response, null, 2)
              }}</pre
            >
          </div>
        </div>

        <!-- HTML capturado -->
        <div v-if="executionResult?.splash_response?.html" class="mb-4">
          <h3 class="text-xs font-medium text-gray-400 mb-2">HTML Capturado</h3>
          <iframe
            :srcdoc="executionResult.splash_response.html"
            class="w-full h-48 border border-[#3e3e42] rounded bg-white"
            sandbox="allow-same-origin"
          />
        </div>

        <!-- Logs/Status -->
        <div v-if="executionResult" class="text-xs text-gray-500 mt-4">
          <p>
            Executado em:
            {{ new Date(executionResult.timestamp * 1000).toLocaleString() }}
          </p>
          <p v-if="executionResult.args_provided" class="mt-1">
            Args: {{ JSON.stringify(executionResult.args_provided) }}
          </p>
        </div>
      </div>

      <!-- Estado vazio -->
      <div v-else class="text-center py-8 text-gray-500 text-sm">
        Execute um script para ver os resultados aqui
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

interface SplashResponse {
  error?: string | object;
  errors?: string[];
  screenshot?: string;
  png?: string;
  html?: string;
  [key: string]: unknown;
}

interface ExecutionResult {
  script_executed: boolean;
  timestamp: number;
  args_provided?: any;
  screenshot_url?: string;
  error?: string;
  script_error?: string;
  details?: string;
  splash_response?: SplashResponse;
}

interface ExecutionStepResult {
  index: number;
  title: string;
  status: "pending" | "running" | "success" | "error";
  log?: string;
  timestamp?: number;
}

interface Props {
  executionResult: ExecutionResult | null;
  executionSteps: ExecutionStepResult[];
}

defineProps<Props>();

defineEmits<{
  "open-screenshot-modal": [url: string];
}>();

const showErrorDetails = ref<boolean>(false);
const showDataDetails = ref<boolean>(false);
</script>
