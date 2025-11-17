import { ref, readonly, computed, watch, onUnmounted, type Ref } from "vue";
import { useWebSocket } from "@vueuse/core";
import { useErrorHandler, type ErrorHandlerOptions } from "./useErrorHandler";

export interface WsMessage {
  type: string;
  session_id?: string;
  timestamp: number;
  step_index?: number;
  step_title?: string;
  status?: string;
  log?: string;
  success?: boolean;
  result?: any;
  error?: string;
  details?: string;
  type_event?: string;
  message?: string;
  progress?: any;
  search_term?: string;
  job_id?: string;
  title?: string;
}

export interface WsClient {
  isConnected: Ref<boolean>;
  connect: (errorOptions?: ErrorHandlerOptions) => Promise<void>;
  disconnect: () => void;
  subscribe: (sessionId?: string) => void;
  onMessage: (callback: (message: WsMessage) => void) => void;
  offMessage: (callback: (message: WsMessage) => void) => void;
}

export const useAsyncExecution = (): WsClient => {
  const config = useRuntimeConfig();
  const { handleWebSocketError } = useErrorHandler();

  const messageCallbacks = ref<Set<(message: WsMessage) => void>>(new Set());
  const errorOptionsRef = ref<ErrorHandlerOptions | undefined>(undefined);
  const isManualDisconnect = ref(false);

  const getWebSocketUrl = (): string => {
    const apiBase = config.public.apiBase as string;

    try {
      const apiUrl = new URL(apiBase);
      const protocol = apiUrl.protocol === "https:" ? "wss:" : "ws:";
      return `${protocol}//${apiUrl.host}/ws/notifications/`;
    } catch (error) {
      console.warn("Invalid apiBase URL, falling back to localhost:", error);
      if (typeof window !== "undefined") {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        return `${protocol}//${window.location.hostname}:8000/ws/notifications/`;
      }
      return "ws://localhost:8000/ws/notifications/";
    }
  };

  const { status, data, send, open, close, ws } = useWebSocket(
    getWebSocketUrl(),
    {
      immediate: false,
      autoReconnect: {
        retries: 5,
        delay: 1000,
        onFailed() {
          handleWebSocketError(
            new Error(
              "Falha na reconexão do WebSocket após múltiplas tentativas"
            ),
            {
              customMessage: "Conexão WebSocket perdida. Recarregue a página.",
              level: "error",
              ...errorOptionsRef.value,
            }
          );
        },
      },
      onConnected() {
        console.log("WebSocket connected");
        isManualDisconnect.value = false;
      },
      onDisconnected(ws, event) {
        console.log("WebSocket disconnected:", event.code, event.reason);
        if (!isManualDisconnect.value && event.code !== 1000) {
          handleWebSocketError(
            new Error(`Conexão perdida (código: ${event.code})`),
            {
              customMessage:
                "Conexão WebSocket perdida. Tentando reconectar...",
              level: "warning",
              ...errorOptionsRef.value,
            }
          );
        }
      },
      onError(ws, event) {
        handleWebSocketError(event, {
          customMessage: "Erro na conexão WebSocket",
          ...errorOptionsRef.value,
        });
      },
    }
  );

  watch(data, (newData) => {
    if (!newData) return;

    try {
      const message: WsMessage = JSON.parse(newData);
      messageCallbacks.value.forEach((callback) => callback(message));
    } catch (error) {
      handleWebSocketError(error, {
        customMessage: "Erro ao processar mensagem do WebSocket",
        ...errorOptionsRef.value,
      });
    }
  });

  const connect = async (errorOptions?: ErrorHandlerOptions): Promise<void> => {
    errorOptionsRef.value = errorOptions;

    try {
      if (status.value === "OPEN") {
        return Promise.resolve();
      }

      open();

      return new Promise((resolve, reject) => {
        const stopWatcher = watch(status, (newStatus) => {
          if (newStatus === "OPEN") {
            stopWatcher();
            resolve();
          } else if (newStatus === "CLOSED" && !isManualDisconnect.value) {
            stopWatcher();
            reject(new Error("Falha ao conectar WebSocket"));
          }
        });

        setTimeout(() => {
          stopWatcher();
          if (status.value !== "OPEN") {
            reject(new Error("Timeout ao conectar WebSocket"));
          }
        }, 5000);
      });
    } catch (error) {
      handleWebSocketError(error, {
        customMessage: "Falha ao criar conexão WebSocket",
        ...errorOptions,
      });
      throw error;
    }
  };

  const disconnect = (): void => {
    isManualDisconnect.value = true;
    close();
  };

  const subscribe = (sessionId?: string): void => {
    if (status.value !== "OPEN" || !ws.value) {
      console.warn("WebSocket not connected, cannot subscribe. Status:", status.value);
      return;
    }

    const subscribeMessage = {
      action: "subscribe",
      session_id: sessionId,
    };

    try {
      send(JSON.stringify(subscribeMessage));
      console.log("Mensagem de inscrição enviada:", subscribeMessage);
    } catch (error) {
      console.error("Erro ao enviar mensagem de inscrição:", error);
    }
  };

  const onMessage = (callback: (message: WsMessage) => void): void => {
    messageCallbacks.value.add(callback);
  };

  const offMessage = (callback: (message: WsMessage) => void): void => {
    messageCallbacks.value.delete(callback);
  };

  const isConnected = computed(() => status.value === "OPEN");

  onUnmounted(() => {
    disconnect();
  });

  return {
    isConnected: readonly(isConnected),
    connect,
    disconnect,
    subscribe,
    onMessage,
    offMessage,
  };
};
