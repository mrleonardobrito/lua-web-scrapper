import { useToast } from "vue-toast-notification";
import type { FetchError } from "ofetch";

export type ErrorLevel = "error" | "warning" | "info" | "success";

export interface ErrorHandlerOptions {
  showLog?: boolean;
  level?: ErrorLevel;
  customMessage?: string;
  duration?: number;
  onError?: (error: unknown) => boolean | void;
  logError?: boolean;
}

export function useErrorHandler() {
  const toast = useToast();

  function extractErrorMessage(error: unknown): string {
    if (typeof error === "object" && error !== null && "response" in error) {
      const fetchError = error as FetchError;
      const data = fetchError.response?._data;

      if (data && typeof data === "object") {
        if ("error" in data && typeof data.error === "string") {
          return data.error;
        }
        if ("message" in data && typeof data.message === "string") {
          return data.message;
        }
        if ("detail" in data && typeof data.detail === "string") {
          return data.detail;
        }
      }

      const status = fetchError.response?.status;
      if (status === 401) return "Não autorizado. Faça login novamente.";
      if (status === 403) return "Acesso negado. Você não tem permissão.";
      if (status === 404) return "Recurso não encontrado.";
      if (status === 422) return "Dados inválidos. Verifique os campos.";
      if (status === 500) return "Erro interno do servidor. Tente novamente.";
      if (status === 503) return "Serviço temporariamente indisponível.";
      if (status === 0 || !status) {
        return "Erro de conexão. Verifique sua internet.";
      }

      return fetchError.message || "Erro desconhecido na requisição.";
    }

    if (error instanceof Error) {
      return error.message;
    }

    if (typeof error === "string") {
      return error;
    }

    return "Ocorreu um erro inesperado.";
  }

  function handleApiError(
    error: unknown,
    options: ErrorHandlerOptions = {}
  ): void {
    const {
      showLog = true,
      level = "error",
      customMessage,
      duration = 5000,
      onError,
      logError = true,
    } = options;

    const message = customMessage || extractErrorMessage(error);

    if (logError && process.client) {
      console.error("[API Error]", {
        error,
        message,
        level,
      });
    }

    if (onError) {
      const result = onError(error);
      if (result === false) {
        return;
      }
    }

    if (showLog && process.client) {
      toast.open({
        message,
        type: level,
        duration,
        position: "top-right",
      });
    }
  }

  function handleWebSocketError(
    error: unknown,
    options: ErrorHandlerOptions = {}
  ): void {
    const {
      showLog = true,
      level = "error",
      customMessage,
      duration = 5000,
      onError,
      logError = true,
    } = options;

    let message = customMessage;

    if (!message) {
      if (error instanceof Error) {
        message = error.message;
      } else if (typeof error === "string") {
        message = error;
      } else {
        message = "Erro na conexão WebSocket.";
      }
    }

    if (logError && process.client) {
      console.error("[WebSocket Error]", {
        error,
        message,
        level,
      });
    }

    if (onError) {
      const result = onError(error);
      if (result === false) {
        return;
      }
    }

    if (showLog && process.client) {
      toast.open({
        message,
        type: level,
        duration,
        position: "top-right",
      });
    }
  }

  function showLog(
    message: string,
    level: ErrorLevel = "info",
    duration: number = 5000
  ): void {
    if (process.client) {
      toast.open({
        message,
        type: level,
        duration,
        position: "top-right",
      });
    }
  }

  return {
    handleApiError,
    handleWebSocketError,
    showLog,
    extractErrorMessage,
  };
}
