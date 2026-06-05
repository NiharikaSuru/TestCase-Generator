import Editor from "@monaco-editor/react";

interface Props {
  code: string;
  language: "python" | "javascript" | "typescript";
  onChange: (value: string) => void;
  theme: "light" | "dark";
}

const MONACO_LANG_MAP: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
};

export default function CodeEditor({ code, language, onChange, theme }: Props) {
  return (
    <div className="overflow-hidden rounded-[22px] border border-slate-200 bg-white shadow-[0_16px_50px_rgba(15,23,42,0.08)] dark:border-slate-800 dark:bg-slate-950/80 dark:shadow-[0_18px_52px_rgba(2,6,23,0.36)]">
      <Editor
        height="360px"
        language={MONACO_LANG_MAP[language] ?? "python"}
        value={code}
        onChange={(val) => onChange(val ?? "")}
        theme={theme === "dark" ? "vs-dark" : "vs"}
        options={{
          fontSize: 13,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: "on",
          lineNumbers: "on",
          automaticLayout: true,
          tabSize: 4,
          padding: { top: 14 },
        }}
      />
    </div>
  );
}
