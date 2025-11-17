<template>
  <div class="fixed top-4 right-4 z-50 space-y-2">
    <TransitionGroup name="log">
      <div
        v-for="log in logs"
        :key="log.id"
        :class="[
          'max-w-sm w-full p-4 rounded-md shadow-lg border',
          getLogColor(log.type),
        ]"
      >
        <div class="flex items-start">
          <div class="flex-1">
            <h4 v-if="log.title" class="font-medium text-sm">
              {{ log.title }}
            </h4>
            <p class="text-sm mt-1">
              {{ log.message }}
            </p>
          </div>
          <button
            class="ml-4 text-gray-400 hover:text-gray-600 transition-colors"
            @click="removeLog(log.id)"
          >
            <svg
              class="w-4 h-4"
              :fill="log.type === 'error' ? 'currentColor' : 'none'"
              :stroke="log.type === 'error' ? 'currentColor' : 'none'"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import {
  useAsyncExecution,
  type WebSocketMessage,
} from "../composables/useAsyncExecution";

interface LogItem {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title?: string;
  message: string;
  timestamp: number;
}

const logs = ref<LogItem[]>([]);

const getLogColor = (type: LogItem["type"]) => {
  switch (type) {
    case "error":
      return "bg-red-50 border-red-200 text-red-800";
    case "success":
      return "bg-green-50 border-green-200 text-green-800";
    case "warning":
      return "bg-yellow-50 border-yellow-200 text-yellow-800";
    case "info":
      return "bg-blue-50 border-blue-200 text-blue-800";
    default:
      return "bg-gray-50 border-gray-200 text-gray-800";
  }
};

const { onMessage, offMessage } = useAsyncExecution();

function handleWebSocketMessage(message: WebSocketMessage) {
  if (
    message.type === "notification_info" ||
    message.type === "notification_error"
  ) {
    const notificationType =
      message.type === "notification_error" ? "error" : "info";

    addLog({
      type: notificationType,
      title: message.title,
      message: message.message || "Notificação recebida",
    });
  }
}

function addLog(notification: Omit<LogItem, "id" | "timestamp">) {
  const newLog: LogItem = {
    id: Date.now().toString(),
    timestamp: Date.now(),
    ...notification,
  };

  logs.value.unshift(newLog);

  setTimeout(() => {
    removeLog(newLog.id);
  }, 5000);

  if (logs.value.length > 5) {
    logs.value = logs.value.slice(0, 5);
  }
}

function removeLog(id: string) {
  const index = logs.value.findIndex((n) => n.id === id);
  if (index > -1) {
    logs.value.splice(index, 1);
  }
}

function showLog(type: LogItem["type"], message: string, title?: string) {
  addLog({ type, message, title });
}

onMounted(() => {
  onMessage(handleWebSocketMessage);
});

onUnmounted(() => {
  offMessage(handleWebSocketMessage);
});

if (typeof window !== "undefined") {
  (window as any).$logs = { show: showLog };
}
</script>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-move {
  transition: transform 0.3s ease;
}
</style>
