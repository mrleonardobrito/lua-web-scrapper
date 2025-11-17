<template>
  <!-- Modal de screenshot em tela cheia -->
  <div
    v-if="selectedScreenshot"
    class="fixed inset-0 bg-black bg-opacity-95 flex items-center justify-center z-50"
    @click="closeModal"
  >
    <div
      class="relative max-w-7xl max-h-screen p-4 w-full h-full flex items-center justify-center"
    >
      <button
        class="absolute top-4 right-4 bg-white/10 hover:bg-white/20 text-white rounded-full p-2 transition-colors z-10"
        aria-label="Fechar"
        @click="closeModal"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
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
      <img
        :src="selectedScreenshot"
        alt="Screenshot completa"
        class="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
        @click.stop
      >
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  selectedScreenshot: string | null;
}

defineProps<Props>();

defineEmits<{
  'close-modal': [];
}>();

function closeModal() {
  emit('close-modal');
}
</script>
