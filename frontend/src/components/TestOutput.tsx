import { useState } from "react";
import { Copy, Check } from "lucide-react";
import Editor from "@monaco-editor/react";

interface TestCase {
  name: string;
  description: string;
  category: string;
  inputs?: string;
  expected_output?: string;
}

interface Props {
  finalTests: string;
  testCode: string;
  testCases: TestCase[];
  language: string;
  framework: string;
  theme: "light" | "dark";
}

export default function TestOutput({ finalTests, testCode, testCases, language, framework: _framework, theme }: Props) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"cases" | "final" | "skeleton">("cases");

  const displayCode = activeTab === "final" ? finalTests : testCode;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(displayCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const monacoLang =
    language === "python" ? "python" : language === "typescript" ? "typescript" : "javascript";

  return (
    <div className="overflow-hidden rounded-[22px] border border-slate-200 bg-white shadow-[0_18px_52px_rgba(15,23,42,0.08)] dark:border-slate-700/40 dark:bg-slate-950/80 dark:shadow-[0_18px_56px_rgba(2,6,23,0.4)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50/80 px-3 py-3 dark:border-slate-700/30 dark:bg-slate-950/70">
        <div className="inline-flex gap-1 rounded-full bg-white p-1 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-600/40">
          <button
            type="button"
            className={`rounded-full px-3 py-1.5 text-[11px] font-semibold transition ${activeTab === "cases" ? "bg-sky-600 text-white shadow-sm dark:bg-sky-500" : "text-slate-500 hover:bg-slate-100 hover:text-sky-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-sky-300"}`}
            onClick={() => setActiveTab("cases")}
          >
            Test Cases
          </button>
          <button
            type="button"
            className={`rounded-full px-3 py-1.5 text-[11px] font-semibold transition ${activeTab === "final" ? "bg-sky-600 text-white shadow-sm dark:bg-sky-500" : "text-slate-500 hover:bg-slate-100 hover:text-sky-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-sky-300"}`}
            onClick={() => setActiveTab("final")}
          >
            Final Tests
          </button>
          {/* <button
            type="button"
            className={`rounded-full px-3 py-1.5 text-[11px] font-semibold transition ${activeTab === "skeleton" ? "bg-sky-600 text-white shadow-sm dark:bg-sky-500" : "text-slate-500 hover:bg-slate-100 hover:text-sky-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-sky-300"}`}
            onClick={() => setActiveTab("skeleton")}
          >
            Skeleton
          </button> */}
        </div>
        {activeTab !== "cases" && (
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[11px] font-semibold text-slate-600 transition hover:-translate-y-0.5 hover:border-sky-300 hover:text-sky-700 dark:border-slate-600/40 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/30 dark:hover:text-sky-300"
            onClick={handleCopy}
            title="Copy to clipboard"
          >
            {copied ? <Check size={16} color="#22c55e" /> : <Copy size={16} />}
            <span>{copied ? "Copied!" : "Copy"}</span>
          </button>
        )}
      </div>
      
      {activeTab === "cases" ? (
        <div className="max-h-[420px] overflow-y-auto p-4">
          <div className="mb-3">
            <h3 className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
              Generated Test Cases <span className="ml-1.5 font-normal text-slate-400 dark:text-slate-500">({testCases.length})</span>
            </h3>
          </div>

          <ul className="space-y-2">
            {testCases.map((tc, i) => {
              const tone =
                tc.category === "happy_path"
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200"
                  : tc.category === "edge_case"
                    ? "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200"
                    : "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-200";

              return (
                <li
                  key={i}
                  className="group rounded-2xl border border-slate-200 bg-white px-3 py-3 transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-sm dark:border-slate-700/40 dark:bg-slate-900/80 dark:hover:border-sky-500/30"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <p className="truncate font-mono text-[11px] font-semibold text-slate-700 dark:text-slate-100">
                        {tc.name}
                      </p>
                      <p className="mt-1 text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                        {tc.description}
                      </p>
                    </div>
                    <span className={`inline-flex self-start rounded-md border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.12em] ${tone}`}>
                      {tc.category.replace("_", " ")}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      ) : (
        <Editor
          height="420px"
          language={monacoLang}
          value={displayCode}
          theme={theme === "dark" ? "vs-dark" : "vs"}
          options={{
            fontSize: 13,
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: "on",
            lineNumbers: "on",
            automaticLayout: true,
            padding: { top: 14 },
          }}
        />
      )}
    </div>
  );
}
