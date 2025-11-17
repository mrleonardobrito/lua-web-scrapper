<template>
  <div class="flex-1 flex flex-col bg-[#1e1e1e]">
    <div
      class="bg-[#2d2d30] border-b border-[#3e3e42] px-4 py-2 flex items-center justify-between"
    >
      <div class="flex items-center gap-3">
        <input
          v-model="scriptName"
          @blur="updateScriptName"
          @keyup.enter="updateScriptName"
          class="bg-transparent text-sm text-gray-300 border-none outline-none focus:bg-[#3e3e42] focus:px-2 focus:py-1 focus:rounded transition-colors"
          :class="{ 'w-32': isEditingName }"
          @focus="isEditingName = true"
          @input="isEditingName = true"
        />
        <span class="text-gray-500">></span>
        <span class="text-sm text-gray-400">script.lua</span>
        <div
          v-if="currentScript?.id && isAuthenticated"
          class="flex items-center gap-1 text-xs ml-4"
        >
          <template v-if="autoSaveStatus === 'saving'">
            <div
              class="animate-spin rounded-full h-3 w-3 border-b-2 border-[#0e639c]"
            />
            <span class="text-[#0e639c]">Salvando...</span>
          </template>
          <template v-else-if="autoSaveStatus === 'saved'">
            <svg
              class="w-3 h-3 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span class="text-green-500">Salvo</span>
          </template>
          <template v-else-if="autoSaveStatus === 'error'">
            <svg
              class="w-3 h-3 text-red-500"
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
            <span class="text-red-500">Erro ao salvar</span>
          </template>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <span>Ln {{ currentLine }}, Col {{ currentCol }}</span>
        <span class="ml-2">Lua</span>
      </div>
    </div>

    <div class="flex-1 flex flex-col overflow-hidden">
      <div
        v-if="currentScript"
        class="bg-[#252526] border-b border-[#3e3e42] p-3 space-y-2"
      >
        <div class="grid grid-cols-3 gap-2">
          <div>
            <label class="block text-xs text-gray-400 mb-1">URL</label>
            <input
              v-model="configUrl"
              type="url"
              placeholder="https://example.com"
              class="w-full px-2 py-1.5 text-sm bg-[#3c3c3c] border border-[#3e3e42] rounded text-gray-300 placeholder-gray-600 focus:outline-none focus:border-[#0e639c]"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1"
              >Wait (segundos)</label
            >
            <input
              v-model.number="configWait"
              type="number"
              min="0"
              max="30"
              class="w-full px-2 py-1.5 text-sm bg-[#3c3c3c] border border-[#3e3e42] rounded text-gray-300 focus:outline-none focus:border-[#0e639c]"
            />
          </div>
          <div class="flex items-end gap-4">
            <label class="flex items-center gap-2 text-xs text-gray-400">
              <input
                v-model="configHtml"
                type="checkbox"
                class="rounded border-[#3e3e42] bg-[#3c3c3c] text-[#0e639c] focus:ring-[#0e639c]"
              />
              Capturar HTML
            </label>
            <label class="flex items-center gap-2 text-xs text-gray-400">
              <input
                v-model="configPng"
                type="checkbox"
                class="rounded border-[#3e3e42] bg-[#3c3c3c] text-[#0e639c] focus:ring-[#0e639c]"
              />
              Screenshot
            </label>
          </div>
        </div>
      </div>

      <!-- Code Editor -->
      <div class="flex-1 relative overflow-hidden">
        <div ref="codeEditorContainer" class="h-full w-full"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { EditorView } from "@codemirror/view";
import { oneDark } from "@codemirror/theme-one-dark";
import { EditorState } from "@codemirror/state";
import {
  lineNumbers,
  highlightActiveLineGutter,
  highlightActiveLine,
  drawSelection,
  dropCursor,
  rectangularSelection,
  crosshairCursor,
  highlightSpecialChars,
  keymap,
} from "@codemirror/view";
import {
  syntaxHighlighting,
  HighlightStyle,
  defaultHighlightStyle,
} from "@codemirror/language";
import { tags } from "@lezer/highlight";
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
} from "@codemirror/commands";
import { EditorSelection } from "@codemirror/state";
import {
  foldGutter,
  indentOnInput,
  bracketMatching,
  foldKeymap,
} from "@codemirror/language";
import {
  closeBrackets,
  autocompletion,
  closeBracketsKeymap,
  completionKeymap,
} from "@codemirror/autocomplete";
import { lintGutter, linter, type Diagnostic } from "@codemirror/lint";
import {
  searchKeymap,
  highlightSelectionMatches as searchHighlight,
} from "@codemirror/search";
import type { Script, ScriptConfig } from "../composables/useLuaScripts";

interface Props {
  isAuthenticated: boolean;
  currentScript: Script | null;
  autoSaveStatus: "idle" | "saving" | "saved" | "error";
}

const props = defineProps<Props>();

const emit = defineEmits<{
  "update-cursor-position": [line: number, col: number];
  "update-code": [code: string];
  "update-config": [config: Partial<ScriptConfig>];
  "update-script-name": [name: string];
}>();

const luaHighlightStyle = HighlightStyle.define([
  { tag: tags.keyword, color: "#C586C0" },
  { tag: tags.string, color: "#CE9178" },
  { tag: tags.comment, color: "#6A9955", fontStyle: "italic" },
  { tag: tags.number, color: "#B5CEA8" },
  { tag: tags.operator, color: "#D4D4D4" },
  { tag: tags.variableName, color: "#9CDCFE" },
  { tag: tags.function(tags.variableName), color: "#DCDCAA" },
  { tag: tags.typeName, color: "#4EC9B0" },
]);

const luaLinter = linter((view) => {
  const diagnostics: Diagnostic[] = [];
  const doc = view.state.doc;
  const text = doc.toString();
  const lines = text.split("\n");

  lines.forEach((line, index) => {
    const lineNum = index + 1;
    const lineStart = doc.line(lineNum).from;

    let openParens = 0;
    let closeParens = 0;
    let openBrackets = 0;
    let closeBrackets = 0;

    for (let i = 0; i < line.length; i++) {
      if (line[i] === "(") openParens++;
      if (line[i] === ")") closeParens++;
      if (line[i] === "[") openBrackets++;
      if (line[i] === "]") closeBrackets++;
    }

    if (openParens !== closeParens) {
      diagnostics.push({
        from: lineStart,
        to: doc.line(lineNum).to,
        severity: "warning",
        message: "Parênteses não balanceados",
      });
    }

    if (openBrackets !== closeBrackets) {
      diagnostics.push({
        from: lineStart,
        to: doc.line(lineNum).to,
        severity: "warning",
        message: "Colchetes não balanceados",
      });
    }
  });

  if (!text.includes("function main")) {
    diagnostics.push({
      from: 0,
      to: Math.min(50, doc.length),
      severity: "info",
      message: "Script deve conter uma função main(splash, args)",
    });
  }

  return diagnostics;
});

const toggleComment = (view: EditorView) => {
  const state = view.state;
  const changes: Array<{ from: number; to: number; insert: string }> = [];
  const newRanges: Array<{ anchor: number; head: number }> = [];

  for (const range of state.selection.ranges) {
    const fromLine = state.doc.lineAt(range.from);
    const toLine = state.doc.lineAt(range.to);

    let allCommented = true;
    const lines: Array<{
      from: number;
      to: number;
      text: string;
      isCommented: boolean;
    }> = [];

    for (let lineNum = fromLine.number; lineNum <= toLine.number; lineNum++) {
      const line = state.doc.line(lineNum);
      const lineText = line.text;
      const trimmed = lineText.trimStart();
      const isCommented = trimmed.startsWith("--");

      if (!isCommented && trimmed.length > 0) {
        allCommented = false;
      }

      lines.push({
        from: line.from,
        to: line.to,
        text: lineText,
        isCommented,
      });
    }

    const shouldComment = !allCommented;

    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i];

      if (shouldComment) {
        if (line.text.trim().length > 0) {
          const indentMatch = line.text.match(/^(\s*)/);
          const indent = indentMatch ? indentMatch[1] : "";
          const content = line.text.slice(indent.length);
          const newText = indent + "-- " + content;
          changes.push({
            from: line.from,
            to: line.to,
            insert: newText,
          });
        }
      } else {
        const trimmed = line.text.trimStart();
        if (trimmed.startsWith("--")) {
          const indentMatch = line.text.match(/^(\s*)/);
          const indent = indentMatch ? indentMatch[1] : "";
          const afterComment = trimmed.slice(2).trimStart();
          const newText = indent + afterComment;
          changes.push({
            from: line.from,
            to: line.to,
            insert: newText,
          });
        }
      }
    }

    let newFrom = range.from;
    let newTo = range.to;

    if (shouldComment) {
      const lineCount = toLine.number - fromLine.number + 1;
      newFrom = range.from;
      newTo = range.to + lineCount * 3;
    } else {
      newFrom = range.from;
      newTo = range.to;
    }

    newRanges.push({ anchor: newFrom, head: newTo });
  }

  if (changes.length > 0) {
    view.dispatch({
      changes,
      selection: EditorSelection.create(
        newRanges.map((r) => EditorSelection.range(r.anchor, r.head))
      ),
    });
    return true;
  }
  return false;
};

const commentKeymap = [
  {
    key: "Mod-/",
    run: toggleComment,
  },
  {
    key: "Ctrl-;",
    run: toggleComment,
  },
];

const codeEditorContainer = ref<HTMLDivElement | null>(null);
let editorView: EditorView | null = null;

const currentScript = computed(() => props.currentScript);
const autoSaveStatus = computed(() => props.autoSaveStatus);
const currentLine = ref(0);
const currentCol = ref(0);
const isEditingName = ref(false);

const scriptName = ref(currentScript.value?.name || "Novo Script");

watch(
  () => currentScript.value?.name,
  (newName) => {
    scriptName.value = newName || "Novo Script";
  }
);

const configHtml = computed({
  get: () => currentScript.value?.config.html ?? false,
  set: (value: boolean) => {
    emit("update-config", { html: value });
  },
});

const configPng = computed({
  get: () => currentScript.value?.config.png ?? false,
  set: (value: boolean) => {
    emit("update-config", { png: value });
  },
});

const configUrl = computed({
  get: () => currentScript.value?.config.url ?? "",
  set: (value: string) => {
    emit("update-config", { url: value });
  },
});

const configWait = computed({
  get: () => currentScript.value?.config.wait ?? 0,
  set: (value: number) => {
    emit("update-config", { wait: value });
  },
});

const defaultScript: Script = {
  id: 0,
  name: "Novo Script",
  code: `-- Digite seu script Lua aqui
-- Exemplo:
-- function main(splash, args)
--   splash:go(args.url)
--   splash:wait(2)
--   return {
--     title = splash:select('title'):text(),
--     url = splash:url()
--   }
-- end`,
  config: {
    url: "",
    wait: 0,
    html: false,
    png: false,
  },
};

onMounted(() => {
  if (!codeEditorContainer.value) return;

  const script = currentScript.value || defaultScript;
  const initialCode = script.code || defaultScript.code;

  const editorExtensions = [
    lineNumbers(),
    highlightActiveLineGutter(),
    highlightSpecialChars(),
    history(),
    foldGutter(),
    drawSelection(),
    dropCursor(),
    EditorState.allowMultipleSelections.of(true),
    indentOnInput(),
    bracketMatching(),
    closeBrackets(),
    autocompletion(),
    rectangularSelection(),
    crosshairCursor(),
    highlightActiveLine(),
    keymap.of([
      ...closeBracketsKeymap,
      ...defaultKeymap,
      ...searchKeymap,
      ...historyKeymap,
      ...foldKeymap,
      ...completionKeymap,
      ...commentKeymap,
      indentWithTab,
    ]),
    searchHighlight(),
    syntaxHighlighting(luaHighlightStyle),
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    lintGutter(),
    luaLinter,
    oneDark,
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        const content = update.state.doc.toString();
        emit("update-code", content);
      }
      if (update.selectionSet) {
        const selection = update.state.selection.main;
        const line = update.state.doc.lineAt(selection.head);
        const col = selection.head - line.from + 1;
        currentLine.value = line.number;
        currentCol.value = col;
        emit("update-cursor-position", line.number, col);
      }
    }),
    EditorView.theme({
      "&": {
        height: "100%",
        fontSize: "14px",
      },
      ".cm-content": {
        padding: "16px",
        minHeight: "100%",
        fontFamily: "'Fira Code', 'Consolas', 'Monaco', monospace",
      },
      ".cm-scroller": {
        overflow: "auto",
      },
      ".cm-focused": {
        outline: "none",
      },
      ".cm-gutters": {
        backgroundColor: "#252526",
        border: "none",
      },
      ".cm-lineNumbers .cm-gutterElement": {
        minWidth: "3ch",
        padding: "0 8px 0 16px",
      },
    }),
  ];

  const startState = EditorState.create({
    doc: initialCode,
    extensions: editorExtensions,
  });

  editorView = new EditorView({
    state: startState,
    parent: codeEditorContainer.value,
  });
});

watch(
  () => currentScript.value?.code,
  (newValue) => {
    if (
      editorView &&
      newValue !== undefined &&
      editorView.state.doc.toString() !== newValue
    ) {
      editorView.dispatch({
        changes: {
          from: 0,
          to: editorView.state.doc.length,
          insert: newValue,
        },
      });
    }
  }
);

const updateScriptName = () => {
  if (scriptName.value.trim() && currentScript.value) {
    emit("update-script-name", scriptName.value.trim());
  } else {
    scriptName.value = currentScript.value?.name || "Novo Script";
  }
};

onBeforeUnmount(() => {
  if (editorView) {
    editorView.destroy();
  }
});

defineExpose({
  codeEditor: codeEditorContainer,
  currentLine,
  currentCol,
});
</script>
