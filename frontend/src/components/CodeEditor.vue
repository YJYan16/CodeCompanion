<template>
  <div ref="editorRef" class="codemirror-container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { basicSetup } from 'codemirror'
import { python } from '@codemirror/lang-python'
import { java } from '@codemirror/lang-java'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView } from '@codemirror/view'
import { EditorState } from '@codemirror/state'

const props = defineProps({
  modelValue: { type: String, default: '' },
  language: { type: String, default: 'python' }
})
const emit = defineEmits(['update:modelValue'])

const editorRef = ref(null)
let view = null

const getLanguageExtension = (lang) => {
  if (lang === 'java') return java()
  return python()
}

const createEditor = (content) => {
  if (view) {
    view.destroy()
    view = null
  }
  
  const doc = content !== undefined ? content : props.modelValue
  
  const state = EditorState.create({
    doc: doc,
    extensions: [
      basicSetup,
      getLanguageExtension(props.language),
      oneDark,
      EditorView.updateListener.of(update => {
        if (update.docChanged) {
          emit('update:modelValue', update.state.doc.toString())
        }
      })
    ]
  })
  view = new EditorView({ state, parent: editorRef.value })
}

onMounted(() => {
  createEditor()
})

watch(() => props.language, () => {
  createEditor(props.modelValue)
})

watch(() => props.modelValue, (newVal) => {
  if (view && view.state.doc.toString() !== newVal) {
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: newVal }
    })
  }
})

onBeforeUnmount(() => {
  view?.destroy()
})
</script>

<style scoped>
.codemirror-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  height: 450px;
  width: 100%;
  max-width: 100%;
}
.codemirror-container :deep(.cm-editor) {
  height: 100% !important;
  width: 100% !important;
  max-width: 100% !important;
}
.codemirror-container :deep(.cm-scroller) {
  overflow: auto !important;
}
.codemirror-container :deep(.cm-content) {
  white-space: pre !important;
  word-wrap: normal !important;
  overflow-wrap: normal !important;
}
</style>