<template>
  <div
    class="h-screen flex flex-col bg-[#1e1e1e] text-gray-100 overflow-hidden"
  >
    <HeaderBar
      :is-executing="isExecuting"
      :lua-script="currentScript?.code || ''"
      @execute="executeScript"
      @clear-editor="clearEditor"
    />

    <div class="flex-1 flex overflow-hidden">
      <FileSidebar
        :is-authenticated="isAuthenticated"
        :user="user"
        :examples="examples"
        :user-scripts="scripts"
        :scripts-loading="loading"
        :current-script-id="currentScript?.id || null"
        @load-example="loadScriptExampleFromSidebar"
        @load-script="loadScriptFromSidebar"
        @create-new-script="createNewScript"
        @login="login"
        @logout="logout"
      />

      <EditorPanel
        :current-script="currentScript"
        :is-authenticated="isAuthenticated"
        :auto-save-status="autoSaveStatus"
        @update-cursor-position="updateCursorPosition"
        @update-code="updateCurrentScriptCode"
        @update-config="updateCurrentScriptConfig"
        @update-script-name="updateScriptName"
      />

      <ResultsPanel
        :execution-result="executionResult"
        :execution-steps="executionSteps"
        @open-screenshot-modal="openScreenshotModal"
      />
    </div>

    <ScreenshotModal
      :selected-screenshot="selectedScreenshot"
      @close-modal="closeScreenshotModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeMount, onBeforeUnmount, watch, nextTick } from "vue";
import { useAuth } from "../composables/useAuth";
import { useLuaScripts } from "../composables/useLuaScripts";
import { useAsyncExecution } from "../composables/useAsyncExecution";

const { user, isAuthenticated, login, logout, checkAuth } = useAuth();
const {
  examples,
  scripts,
  loading,
  currentScript,
  isExecuting,
  lastResult,
  executeScript: executeLuaScript,
  finishExecution,
  loadExample,
  loadScript,
  createNewScript: createNewScriptFromComposable,
  updateCurrentScriptCode,
  updateCurrentScriptConfig,
  updateCurrentScriptName,
  createScript,
  updateScript,
  fetchScripts,
} = useLuaScripts();

const autoSaveStatus = ref<"idle" | "saving" | "saved" | "error">("idle");
const currentLine = ref(0);
const currentCol = ref(0);

// Propriedades para resultados de execução
const executionResult = ref(null);
const executionSteps = ref([]);
const selectedScreenshot = ref(null);

// WebSocket para execução assíncrona
const { onMessage, offMessage, connect, subscribe, isConnected, disconnect } =
  useAsyncExecution();

// Timeout para detectar ausência de mensagens
let messageTimeout: NodeJS.Timeout | null = null;
let lastMessageTime: number | null = null;
const MESSAGE_TIMEOUT_MS = 60000; // 60 segundos sem mensagens

// Resetar timeout quando receber mensagem
const resetMessageTimeout = () => {
  lastMessageTime = Date.now();
  if (messageTimeout) {
    clearTimeout(messageTimeout);
  }

  // Configurar timeout para fechar conexão se não receber mensagens
  messageTimeout = setTimeout(() => {
    const timeSinceLastMessage = lastMessageTime
      ? Date.now() - lastMessageTime
      : MESSAGE_TIMEOUT_MS;

    if (timeSinceLastMessage >= MESSAGE_TIMEOUT_MS) {
      console.warn(
        `Nenhuma mensagem recebida por ${
          MESSAGE_TIMEOUT_MS / 1000
        } segundos. Fechando conexão WebSocket.`
      );
      finishExecution();
      disconnect();

      executionResult.value = {
        script_executed: false,
        error: `Timeout: Nenhuma mensagem recebida do servidor por ${
          MESSAGE_TIMEOUT_MS / 1000
        } segundos`,
        timestamp: Date.now() / 1000,
      };
    }
  }, MESSAGE_TIMEOUT_MS);
};

// Handler para mensagens WebSocket
const handleWebSocketMessage = (message) => {
  console.log("WebSocket message received:", message);

  // Resetar timeout ao receber qualquer mensagem
  resetMessageTimeout();

  // Verificar se é uma mensagem de execução Lua
  if (
    message.type === "lua_execution_progress" ||
    message.type === "lua_execution_step"
  ) {
    // Atualizar passos de execução
    const stepIndex = executionSteps.value.findIndex(
      (step) => step.index === message.step_index
    );
    if (stepIndex >= 0) {
      executionSteps.value[stepIndex] = {
        ...executionSteps.value[stepIndex],
        status: message.status || "running",
        log: message.log || message.message,
        timestamp: message.timestamp,
      };
    } else {
      // Novo passo
      executionSteps.value.push({
        index: message.step_index || executionSteps.value.length,
        title:
          message.step_title ||
          message.title ||
          `Passo ${message.step_index || executionSteps.value.length}`,
        status: message.status || "running",
        log: message.log || message.message,
        timestamp: message.timestamp,
      });
    }
  } else if (
    message.type === "lua_execution_completed" ||
    message.type === "lua_execution_complete" ||
    message.type === "execution_result"
  ) {
    // Atualizar resultado final e finalizar execução
    finishExecution();
    // Limpar timeout pois a execução terminou
    if (messageTimeout) {
      clearTimeout(messageTimeout);
      messageTimeout = null;
    }

    console.log("Resultado completo recebido:", message);

    if (message.result) {
      // O resultado já está no formato esperado com todas as propriedades
      // Incluindo screenshot_url, splash_response, etc.
      executionResult.value = {
        ...message.result,
        // Garantir que script_executed está definido
        script_executed: message.result.script_executed !== false,
        // Garantir que timestamp está presente
        timestamp:
          message.result.timestamp || message.timestamp || Date.now() / 1000,
      };
      console.log("Resultado processado:", executionResult.value);
    } else if (message.data) {
      executionResult.value = {
        ...message.data,
        script_executed: message.data.script_executed !== false,
        timestamp:
          message.data.timestamp || message.timestamp || Date.now() / 1000,
      };
    } else if (message.splash_response) {
      executionResult.value = {
        script_executed: true,
        timestamp: message.timestamp || Date.now() / 1000,
        splash_response: message.splash_response,
        args_provided: message.args_provided,
        screenshot_url: message.screenshot_url,
      };
    } else if (message.success) {
      // Mensagem de sucesso sem resultado detalhado
      executionResult.value = {
        script_executed: true,
        timestamp: message.timestamp || Date.now() / 1000,
        success: true,
      };
    }
  } else if (message.type === "lua_execution_error") {
    // Erro na execução
    finishExecution();
    // Limpar timeout pois a execução terminou (com erro)
    if (messageTimeout) {
      clearTimeout(messageTimeout);
      messageTimeout = null;
    }

    executionResult.value = {
      script_executed: false,
      error: message.error || message.message || "Erro na execução",
      timestamp: message.timestamp || Date.now() / 1000,
    };
  } else if (message.type === "step_update") {
    // Compatibilidade com mensagens antigas
    const stepIndex = executionSteps.value.findIndex(
      (step) => step.index === message.step_index
    );
    if (stepIndex >= 0) {
      executionSteps.value[stepIndex] = {
        ...executionSteps.value[stepIndex],
        status: message.status || "running",
        log: message.log || message.message,
        timestamp: message.timestamp,
      };
    } else {
      executionSteps.value.push({
        index: message.step_index,
        title: message.step_title || `Passo ${message.step_index}`,
        status: message.status || "running",
        log: message.log || message.message,
        timestamp: message.timestamp,
      });
    }
  } else if (message.type === "execution_complete") {
    finishExecution();
    // Limpar timeout pois a execução terminou
    if (messageTimeout) {
      clearTimeout(messageTimeout);
      messageTimeout = null;
    }

    if (message.result) {
      executionResult.value = message.result;
    }
  } else if (message.type === "subscribed") {
    console.log("Inscrito com sucesso na sessão:", message.session_id);
    // Resetar timeout ao confirmar inscrição
    resetMessageTimeout();
  } else if (message.type === "error") {
    console.error("Erro recebido via WebSocket:", message.message);
    // Resetar timeout mesmo em caso de erro
    resetMessageTimeout();
  }
};

const loadScriptExampleFromSidebar = async (exampleId: string) => {
  // Cancelar auto-save pendente antes de trocar de script
  if (autoSaveTimeout) {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = null;
  }

  await loadExample(exampleId);
  // Recarregar scripts para verificar se já existe um com o mesmo nome (apenas se autenticado)
  if (isAuthenticated.value) {
    try {
      await fetchScripts();
    } catch (error) {
      console.error("Erro ao buscar scripts:", error);
    }
  }
  // Verificar novamente após carregar scripts
  const example = examples.value.find((ex) => ex.id === Number(exampleId));
  if (example && currentScript.value) {
    const existingScript = scripts.value.find((s) => s.name === example.name);
    if (existingScript && currentScript.value.id === 0) {
      // Se encontrou um script existente e o currentScript ainda é novo, carregar o existente
      loadScript(existingScript.id);
    }
  }
};

const loadScriptFromSidebar = (scriptId: number) => {
  // Cancelar auto-save pendente antes de trocar de script
  if (autoSaveTimeout) {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = null;
  }

  loadScript(scriptId);
};

const createNewScript = () => {
  // Cancelar auto-save pendente antes de criar novo script
  if (autoSaveTimeout) {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = null;
  }

  createNewScriptFromComposable();
};

const clearEditor = () => {
  createNewScriptFromComposable();
};

const executeScript = async () => {
  if (!currentScript.value) return;

  // Validar se URL está preenchida
  if (
    !currentScript.value.config.url ||
    currentScript.value.config.url.trim() === ""
  ) {
    alert("Por favor, preencha a URL antes de executar o script.");
    return;
  }

  // Limpar resultados anteriores
  executionResult.value = null;
  executionSteps.value = [];

  // Usar o código atual do script (que pode ter sido modificado no editor)
  const scriptCode = currentScript.value.code;

  // Extrair passos dos comentários do script (se houver)
  const steps: Array<{ index: number; title: string; commentLine: number }> =
    [];
  const lines = scriptCode.split("\n");
  let stepIndex = 0;
  lines.forEach((line, lineIndex) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("--")) {
      const title = trimmed.substring(2).trim();
      if (title) {
        steps.push({
          index: stepIndex++,
          title,
          commentLine: lineIndex + 1,
        });
      }
    }
  });

  // Garantir que o WebSocket está conectado
  if (!isConnected.value) {
    try {
      await connect();
    } catch (error) {
      console.error("Erro ao conectar WebSocket:", error);
      alert(
        "Erro ao conectar WebSocket. Não será possível receber atualizações da execução."
      );
      return;
    }
  }

  // Gerar session_id no frontend ANTES de iniciar a execução
  const sessionId = crypto.randomUUID();
  console.log("Session ID gerado:", sessionId);

  // Inscrever-se ANTES de iniciar a execução para evitar condição de corrida
  console.log("Inscrevendo-se na sessão ANTES de iniciar:", sessionId);
  subscribe(sessionId);

  // Aguardar confirmação de inscrição (com timeout de segurança)
  await new Promise<void>((resolve) => {
    const checkSubscribed = (message: any) => {
      if (message.type === "subscribed" && message.session_id === sessionId) {
        offMessage(checkSubscribed);
        console.log("Inscrição confirmada, iniciando execução");
        resolve();
      }
    };
    onMessage(checkSubscribed);

    // Timeout de segurança - continuar mesmo se não receber confirmação
    setTimeout(() => {
      offMessage(checkSubscribed);
      console.warn(
        "Timeout aguardando confirmação de inscrição, continuando mesmo assim"
      );
      resolve();
    }, 2000);
  });

  // Limpar timeout anterior se houver
  if (messageTimeout) {
    clearTimeout(messageTimeout);
    messageTimeout = null;
  }

  // Iniciar execução assíncrona PASSANDO o session_id gerado
  const result = await executeLuaScript(
    scriptCode,
    currentScript.value.config,
    steps,
    sessionId
  );

  if (result.success) {
    // Iniciar timeout para detectar ausência de mensagens
    resetMessageTimeout();
  } else {
    // Se houve erro, definir isExecuting como false
    finishExecution();
    if (result.error) {
      executionResult.value = {
        error: result.error,
        script_executed: false,
        timestamp: Date.now() / 1000,
      };
    }
  }
};

const updateCursorPosition = (line: number, col: number) => {
  currentLine.value = line;
  currentCol.value = col;
};

const openScreenshotModal = (url: string) => {
  selectedScreenshot.value = url;
};

const closeScreenshotModal = () => {
  selectedScreenshot.value = null;
};

const updateScriptName = (name: string) => {
  if (currentScript.value) {
    updateCurrentScriptName(name);
  }
};

// Auto-save functionality
let autoSaveTimeout: NodeJS.Timeout | null = null;
let isAutoSaving = false; // Flag para evitar múltiplas execuções simultâneas

const autoSaveScript = async () => {
  if (!currentScript.value || !isAuthenticated.value) return;

  // Evitar múltiplas execuções simultâneas
  if (isAutoSaving) {
    return;
  }

  // Validação: garantir que nome e código existam
  const scriptName = (currentScript.value.name?.trim() || "Novo Script").trim();
  const scriptCode = (currentScript.value.code || "").trim();

  // Não salvar se não houver código
  if (!scriptCode) {
    return;
  }

  // Garantir que o nome não esteja vazio
  if (!scriptName || scriptName === "") {
    return; // Não tenta salvar sem nome válido
  }

  isAutoSaving = true;
  autoSaveStatus.value = "saving";

  try {
    if (currentScript.value.id && currentScript.value.id > 0) {
      // Atualizar script existente
      await updateScript(currentScript.value.id, {
        name: scriptName,
        code: scriptCode,
      });
    } else {
      // Criar novo script
      const savedScript = await createScript(
        scriptName,
        scriptCode,
        currentScript.value.config
      );
      // Atualizar o currentScript com o ID do script salvo
      // O loadScript vai carregar o script completo, incluindo o nome gerado automaticamente
      if (savedScript.id) {
        // Recarregar lista de scripts para refletir o novo script (apenas se autenticado)
        if (isAuthenticated.value) {
          try {
            await fetchScripts();
          } catch (error) {
            console.error("Erro ao buscar scripts:", error);
          }
        }
        // Cancelar qualquer auto-save pendente antes de carregar o script
        if (autoSaveTimeout) {
          clearTimeout(autoSaveTimeout);
          autoSaveTimeout = null;
        }
        loadScript(savedScript.id);
      }
    }
    autoSaveStatus.value = "saved";
  } catch (error: any) {
    // Verificar se é erro de nome duplicado (para nome customizado)
    const isDuplicateNameError =
      error?.response?._data?.name &&
      Array.isArray(error.response._data.name) &&
      error.response._data.name.some(
        (err: any) =>
          typeof err === "string" &&
          err.includes("Você já possui um script com este nome")
      );

    if (isDuplicateNameError) {
      // Para nome customizado duplicado, não mostrar erro no auto-save
      // O usuário pode renomear manualmente
      console.warn(
        "Nome de script duplicado, não foi possível salvar automaticamente:",
        scriptName
      );
      autoSaveStatus.value = "error";
    } else {
      console.error("Erro no auto-save:", error);
      autoSaveStatus.value = "error";
    }
  } finally {
    isAutoSaving = false;
  }

  // Reset status após 3 segundos
  setTimeout(() => {
    if (autoSaveStatus.value === "saved") {
      autoSaveStatus.value = "idle";
    }
  }, 3000);
};

const scheduleAutoSave = () => {
  // Não agendar se já estiver salvando
  if (isAutoSaving) {
    return;
  }

  if (autoSaveTimeout) {
    clearTimeout(autoSaveTimeout);
  }
  autoSaveTimeout = setTimeout(autoSaveScript, 1000); // Salvar após 1 segundo de inatividade
};

// Watchers para auto-save
watch(
  () => currentScript.value?.code,
  () => {
    if (currentScript.value?.code) {
      scheduleAutoSave();
    }
  },
  { deep: true }
);

watch(
  () => currentScript.value?.name,
  () => {
    if (currentScript.value?.name) {
      scheduleAutoSave();
    }
  }
);

watch(
  () => currentScript.value?.config,
  () => {
    if (currentScript.value?.config) {
      scheduleAutoSave();
    }
  },
  { deep: true }
);

// Watcher para buscar scripts quando o usuário faz login
watch(
  () => isAuthenticated.value,
  async (newValue, oldValue) => {
    // Quando o usuário faz login (muda de false para true)
    if (newValue && !oldValue) {
      try {
        await fetchScripts();
      } catch (error) {
        console.error("Erro ao buscar scripts após login:", error);
      }
    }
  }
);

onBeforeMount(async () => {
  const wasAuthenticated = await checkAuth();

  // Criar um script inicial se não houver nenhum
  if (!currentScript.value) {
    createNewScript();
  }

  // Se já estava autenticado, buscar scripts
  if (wasAuthenticated) {
    try {
      await fetchScripts();
    } catch (error) {
      console.error("Erro ao buscar scripts:", error);
    }
  }

  // Conectar WebSocket e registrar handler de mensagens
  try {
    await connect();
    onMessage(handleWebSocketMessage);
  } catch (error) {
    console.warn("Falha ao conectar WebSocket:", error);
  }
});

// Watcher para debug do resultado
watch(
  () => executionResult.value,
  (newResult) => {
    if (newResult) {
      console.log("executionResult atualizado:", {
        script_executed: newResult.script_executed,
        has_screenshot_url: !!newResult.screenshot_url,
        has_splash_response: !!newResult.splash_response,
        screenshot_url: newResult.screenshot_url,
        timestamp: newResult.timestamp,
      });
    }
  },
  { deep: true }
);

// Limpar timeout ao desmontar componente
onBeforeUnmount(() => {
  if (messageTimeout) {
    clearTimeout(messageTimeout);
    messageTimeout = null;
  }
});
</script>
