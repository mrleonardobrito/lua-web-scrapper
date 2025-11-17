import { ref, readonly } from "vue";
import { useApi } from "./useApi";

// ============================================================================
// Interfaces e Tipos
// ============================================================================

export interface ScriptExecution {
  id: number;
  script: number;
  script_name: string;
  status: "pending" | "running" | "success" | "error";
  started_at: string;
  finished_at: string | null;
  request_args: Record<string, any>;
  response_data: Record<string, any> | null;
  logs: string;
  screenshot_url: string | null;
  duration: number | null;
}

export interface LuaExecutionArgs {
  url?: string;
  wait?: number;
  html?: boolean;
  png?: boolean;
  [key: string]: any;
}

export interface LuaExecutionResult {
  script_executed: boolean;
  timestamp: number;
  args_provided?: LuaExecutionArgs;
  splash_response?: any;
  screenshot_url?: string;
  error?: string;
  script_error?: string;
}

export interface ScriptHistoryEntry {
  name: string;
  code: string;
  config: ScriptConfig;
  savedAt: number;
}

export interface Script {
  id: number;
  name: string;
  code: string;
  config: ScriptConfig;
}

export interface ScriptConfig {
  url: string;
  wait: number;
  html: boolean;
  png: boolean;
}

export interface ScriptStep {
  index: number;
  title: string;
  commentLine: number;
}

const DEFAULT_SCRIPT_TEMPLATE = `function main(splash, args)
  -- Script básico de exemplo
  -- Visite uma URL e retorne informações básicas
  splash:go(args.url or "https://httpbin.org/html")
  splash:wait(args.wait or 1)

  return {
    url = splash:url(),
    title = splash:select('title') and splash:select('title'):text() or "Sem título",
    status = "Executado com sucesso"
  }
end`;

const DEFAULT_SCRIPT_CONFIG: ScriptConfig = {
  url: "",
  wait: 0,
  html: false,
  png: false,
};

const EXAMPLE_SCRIPTS: Script[] = [
  {
    id: 1,
    name: "Screenshot do meu site",
    code: `function main(splash, args)
  splash:go("https://www.mrleonardobrito.com/")
  splash:wait(3)
  local screenshot = splash:png()
  return { screenshot = screenshot }
end`,
    config: {
      url: "https://www.mrleonardobrito.com/",
      wait: 3,
      html: false,
      png: true,
    },
  },
  {
    id: 2,
    name: "Wikipedia aleatória",
    code: `function main(splash, args)
  splash:go("https://pt.wikipedia.org/wiki/Especial:Aleat%C3%B3ria")
  splash:wait(2)
  local screenshot = splash:png()
  return { screenshot = screenshot }
end`,
    config: {
      url: "https://pt.wikipedia.org/wiki/Especial:Aleat%C3%B3ria",
      wait: 2,
      html: false,
      png: true,
    },
  },
];
function createDefaultScript(name: string = "Novo Script"): Script {
  return {
    id: 0,
    name,
    code: DEFAULT_SCRIPT_TEMPLATE,
    config: { ...DEFAULT_SCRIPT_CONFIG },
  };
}

function createErrorResult(error: string): LuaExecutionResult {
  return {
    script_executed: false,
    timestamp: Date.now() / 1000,
    error,
  };
}

function validateScript(script: string): { valid: boolean; error?: string } {
  if (!script.trim()) {
    return { valid: false, error: "Script Lua é obrigatório" };
  }

  if (!script.includes("function main")) {
    return {
      valid: false,
      error: "Script deve conter uma função main(splash, args)",
    };
  }

  return { valid: true };
}

export const useLuaScripts = () => {
  const { get, post, patch } = useApi();

  const scripts = ref<Script[]>([]);
  const loading = ref(false);
  const isExecuting = ref(false);
  const currentScript = ref<Script | null>(null);
  const lastResult = ref<LuaExecutionResult | null>(null);
  const examples = ref<Script[]>([...EXAMPLE_SCRIPTS]);

  const fetchScripts = async (): Promise<Script[]> => {
    loading.value = true;
    try {
      const data = await get<Script[]>("/api/scripts/");
      scripts.value = data;
      return data;
    } catch (error) {
      console.error("Erro ao buscar scripts:", error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const fetchScriptDetails = async (
    scriptId: number
  ): Promise<{ script: Script; execution: ScriptExecution | null }> => {
    try {
      const [script, execution] = await Promise.all([
        get<Script>(`/api/scripts/${scriptId}/`),
        get<ScriptExecution | null>(
          `/api/scripts/${scriptId}/executions/latest/`
        ).catch(() => null),
      ]);

      return { script, execution };
    } catch (error) {
      console.error("Erro ao buscar detalhes do script:", error);
      throw error;
    }
  };

  const createScript = async (
    name: string,
    code: string,
    config?: Partial<ScriptConfig>
  ): Promise<Script> => {
    // Validação dos campos obrigatórios
    let scriptName = (name || "").trim();
    const scriptCode = (code || "").trim();

    if (!scriptCode) {
      throw new Error("O código do script é obrigatório");
    }

    // Se não houver nome, usar padrão
    if (!scriptName) {
      scriptName = "Novo Script";
    }

    // Tentar criar o script, gerando nome único se necessário
    let attempts = 0;
    const MAX_ATTEMPTS = 10;
    const isDefaultName =
      scriptName === "Novo Script" || /^Novo Script \(\d+\)$/.test(scriptName);
    const originalName = scriptName;

    while (attempts < MAX_ATTEMPTS) {
      try {
        const data = await post<Script>(
          "/api/scripts/",
          {
            name: scriptName,
            code: scriptCode,
            config: config || DEFAULT_SCRIPT_CONFIG,
          },
          {},
          { showLog: false, logError: false } // Não mostrar erro genérico, vamos tratar especificamente
        );
        return data;
      } catch (error: any) {
        // Verificar se é erro de nome duplicado
        const isDuplicateNameError =
          error?.response?._data?.name &&
          Array.isArray(error.response._data.name) &&
          error.response._data.name.some(
            (err: any) =>
              typeof err === "string" &&
              err.includes("Você já possui um script com este nome")
          );

        if (isDuplicateNameError) {
          // Se for nome padrão, tentar com número
          if (isDefaultName) {
            attempts++;
            scriptName = `Novo Script (${attempts})`;
          } else {
            // Para outros nomes (incluindo exemplos), também gerar nome único
            attempts++;
            scriptName = `${originalName} (${attempts})`;
          }

          if (attempts >= MAX_ATTEMPTS) {
            // Se exceder tentativas, lançar erro
            console.error(
              "Não foi possível gerar um nome único após várias tentativas"
            );
            throw new Error(
              "Não foi possível criar script: muitos scripts com este nome existem"
            );
          }
          // Continuar loop para tentar novamente
          continue;
        } else {
          // Se não for erro de nome duplicado, lançar erro
          console.error("Erro ao criar script:", error);
          throw error;
        }
      }
    }

    // Não deveria chegar aqui, mas por segurança
    throw new Error("Erro inesperado ao criar script");
  };

  const updateScript = async (
    scriptId: number,
    updates: Partial<Pick<Script, "name" | "code">>
  ): Promise<Script> => {
    try {
      const data = await patch<Script>(`/api/scripts/${scriptId}/`, {
        ...updates,
      });
      return data;
    } catch (error) {
      console.error("Erro ao atualizar script:", error);
      throw error;
    }
  };

  const executeScript = async (
    script: string,
    args: LuaExecutionArgs = {},
    steps: Array<{ index: number; title: string; commentLine: number }> = [],
    sessionId?: string
  ): Promise<{ success: boolean; sessionId?: string; error?: string }> => {
    const validation = validateScript(script);
    if (!validation.valid) {
      lastResult.value = createErrorResult(validation.error!);
      return { success: false, error: validation.error };
    }

    isExecuting.value = true;
    lastResult.value = null;

    try {
      const response = await post<{
        session_id: string;
        job_id: string;
        status: string;
        message: string;
      }>("/api/lua/execute/", {
        script,
        args,
        steps,
        session_id: sessionId,
        script_id:
          currentScript.value?.id && currentScript.value.id > 0
            ? currentScript.value.id
            : undefined,
      });

      if (response.session_id) {
        return { success: true, sessionId: response.session_id };
      }

      return { success: false, error: "Session ID não recebido" };
    } catch (err: any) {
      console.error("Erro ao executar script Lua:", err);
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido";
      lastResult.value = createErrorResult(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      // Não definir isExecuting como false aqui, pois a execução é assíncrona
      // Será definido como false quando receber a mensagem de conclusão via WebSocket
    }
  };

  const clearResults = () => {
    lastResult.value = null;
  };

  const loadExample = async (exampleId: string | number) => {
    const example = examples.value.find((ex) => ex.id === Number(exampleId));
    console.log("Loading example:", exampleId, example);
    if (example) {
      // Verificar se já existe um script salvo com este nome
      const existingScript = scripts.value.find((s) => s.name === example.name);

      if (existingScript) {
        // Se já existe, carregar o script existente
        currentScript.value = { ...existingScript };
      } else {
        // Se não existe, criar um novo com o exemplo (mas não salvar ainda)
        currentScript.value = {
          ...example,
          id: 0,
        };
      }
    }
  };

  const loadScript = (scriptId: number) => {
    const script = scripts.value.find((s) => s.id === scriptId);
    if (script) {
      currentScript.value = { ...script };
    }
  };

  const createNewScript = () => {
    currentScript.value = createDefaultScript();
  };

  const updateCurrentScriptCode = (code: string) => {
    if (currentScript.value) {
      currentScript.value = {
        ...currentScript.value,
        code,
      };
    }
  };

  const updateCurrentScriptConfig = (config: Partial<ScriptConfig>) => {
    if (currentScript.value) {
      currentScript.value = {
        ...currentScript.value,
        config: {
          ...currentScript.value.config,
          ...config,
        },
      };
    }
  };

  const updateCurrentScriptName = (name: string) => {
    if (currentScript.value) {
      currentScript.value = {
        ...currentScript.value,
        name,
      };
    }
  };

  const finishExecution = () => {
    isExecuting.value = false;
  };

  return {
    scripts: readonly(scripts),
    loading: readonly(loading),
    isExecuting: readonly(isExecuting),
    currentScript: readonly(currentScript),
    lastResult: readonly(lastResult),
    examples: readonly(examples),

    fetchScripts,
    fetchScriptDetails,
    createScript,
    updateScript,

    executeScript,
    clearResults,
    finishExecution,

    loadExample,
    loadScript,
    createNewScript,
    updateCurrentScriptCode,
    updateCurrentScriptConfig,
    updateCurrentScriptName,
  };
};
