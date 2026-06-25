import Editor, { type OnMount } from '@monaco-editor/react';

interface CodeEditorProps {
  value: string;
  onChange: (v: string) => void;
  readOnly?: boolean;
  height?: string;
  drillId?: string;
  /** Monaco language id, e.g. 'python' or 'csharp'. */
  language?: string;
  /** When false, skip the outer editor-shell border (parent provides chrome). */
  chrome?: boolean;
}

/** Convert Kumon ___ markers into Monaco tab-stop placeholders. */
function toSnippet(code: string): string {
  let n = 1;
  return code.replace(/___/g, () => `\${${n++}:}`);
}

export function CodeEditor({ value, onChange, readOnly, height = '280px', drillId, language = 'python', chrome = true }: CodeEditorProps) {
  const handleMount: OnMount = (editor) => {
    if (!value.includes('___')) return;

    const snippet = toSnippet(value);
    editor.setValue('');
    editor.trigger('codenda', 'editor.action.insertSnippet', {
      snippet,
      language,
    });
    onChange(editor.getValue());
  };

  return (
    <div className={chrome ? 'editor-shell' : 'rounded-lg'}>
      <Editor
        key={`${drillId ?? 'editor'}-${language}`}
        height={height}
        language={language}
        theme="vs-dark"
        defaultValue={value}
        onChange={(v) => onChange(v ?? '')}
        onMount={handleMount}
        options={{
          readOnly,
          minimap: { enabled: false },
          scrollbar: { alwaysConsumeMouseWheel: false },
          fontSize: 14,
          fontFamily: '"JetBrains Mono", ui-monospace, monospace',
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          snippetSuggestions: 'none',
          wordBasedSuggestions: 'off',
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: 'line',
          cursorBlinking: 'smooth',
        }}
      />
    </div>
  );
}
