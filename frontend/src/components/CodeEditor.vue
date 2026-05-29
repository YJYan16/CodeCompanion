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

onMounted(() => {
  const langExt = props.language === 'java' ? java() : python()
  const state = EditorState.create({
    doc: props.modelValue,
    extensions: [
      basicSetup,
      langExt,
      oneDark,
      EditorView.updateListener.of(u => {
        if (u.docChanged) emit('update:modelValue', u.state.doc.toString())
      })
    ]
  })
  view = new EditorView({ state, parent: editorRef.value })
})

// 监听 modelValue 变化，更新编辑器内容
watch(() => props.modelValue, (newValue) => {
  if (view && view.state.doc.toString() !== newValue) {
    view.dispatch({
      changes: {
        from: 0,
        to: view.state.doc.length,
        insert: newValue
      }
    })
  }
})

onBeforeUnmount(() => view?.destroy())
</script>

<style scoped>
.codemirror-container {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  height: 400px;
  width: 100%;
  transition: all 0.3s ease;
  box-shadow: 0 0 0 rgba(102, 126, 234, 0);
}
.codemirror-container:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.15);
}
.codemirror-container :deep(.cm-editor) {
  height: 100%;
  width: 100%;
}
.codemirror-container :deep(.cm-scroller) {
  overflow: auto;
}
</style>