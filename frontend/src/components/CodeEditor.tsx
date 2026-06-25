import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  value: string;
  onChange: (v: string) => void;
  readOnly?: boolean;
  height?: string;
}

export function CodeEditor({ value, onChange, readOnly, height = '280px' }: CodeEditorProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-600">
      <Editor
        height={height}
        language="python"
        theme="vs-dark"
        value={value}
        onChange={(v) => onChange(v ?? '')}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
        }}
      />
    </div>
  );
}
