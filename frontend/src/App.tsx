import { useEffect, useState } from "react";
import { FlaskConical, Loader2, MoonStar, Sparkles, SunMedium, Code, CheckCheck } from "lucide-react";
import CodeEditor from "./components/CodeEditor";
import LanguageSelector from "./components/LanguageSelector";
import TestOutput from "./components/TestOutput";
import { generateTests, type GenerateTestResponse } from "./api/client";

const PYTHON_PLACEHOLDER = `def calculate_discount(price: float, discount_percent: float) -> float:
    """Apply a percentage discount to a price."""
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)`;

const JS_PLACEHOLDER = `function calculateDiscount(price, discountPercent) {
  if (price < 0) throw new Error("Price cannot be negative");
  if (discountPercent < 0 || discountPercent > 100)
    throw new Error("Discount must be between 0 and 100");
  return price * (1 - discountPercent / 100);
}

module.exports = { calculateDiscount };`;

const TS_PLACEHOLDER = `export function calculateDiscount(price: number, discountPercent: number): number {
  if (price < 0) throw new Error("Price cannot be negative");
  if (discountPercent < 0 || discountPercent > 100)
    throw new Error("Discount must be between 0 and 100");
  return price * (1 - discountPercent / 100);
}`;

const PLACEHOLDERS: Record<string, string> = {
  python: PYTHON_PLACEHOLDER,
  javascript: JS_PLACEHOLDER,
  typescript: TS_PLACEHOLDER,
};

type ThemeMode = "light" | "dark";

function App() {
  const [language, setLanguage] = useState<"python" | "javascript" | "typescript">("python");
  const [code, setCode] = useState(PYTHON_PLACEHOLDER);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<GenerateTestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<ThemeMode>("light");
  const [loadingStep, setLoadingStep] = useState(0);
  const [maxLoadingStep, setMaxLoadingStep] = useState(0);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem("utc-theme");
    const preferredDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setTheme(savedTheme === "dark" || (!savedTheme && preferredDark) ? "dark" : "light");
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("utc-theme", theme);
  }, [theme]);

  // Cycle through loading steps every 2.5 seconds
  useEffect(() => {
    if (!isLoading) {
      setLoadingStep(0);
      setMaxLoadingStep(0);
      return;
    }

    const interval = setInterval(() => {
      setLoadingStep((prev) => {
        const next = (prev + 1) % 4;
        setMaxLoadingStep((max) => Math.max(max, next));
        return next;
      });
    }, 2500);

    return () => clearInterval(interval);
  }, [isLoading]);

  const handleLanguageChange = (lang: "python" | "javascript" | "typescript") => {
    setLanguage(lang);
    setCode(PLACEHOLDERS[lang]);
    setResult(null);
    setError(null);
  };

  const handleGenerate = async () => {
    if (!code.trim()) return;
    setIsLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await generateTests({ code, language });
      setResult(data);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "An unexpected error occurred. Please try again.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTheme = () => {
    setTheme((current) => (current === "light" ? "dark" : "light"));
  };

  return (
    <div className="min-h-screen px-3 py-3 text-slate-900 dark:text-slate-100 sm:px-4 sm:py-4">
      <div className="mx-auto flex min-h-[calc(100vh-1.5rem)] w-full max-w-7xl flex-col overflow-hidden rounded-[28px] border border-white/60 bg-white/75 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur-xl dark:border-slate-700/30 dark:bg-slate-950/55 dark:shadow-[0_28px_90px_rgba(2,6,23,0.55)]">
        <header className="border-b border-sky-100/80 bg-white/70 px-4 py-4 dark:border-slate-700/30 dark:bg-slate-950/45 sm:px-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-sky-100 p-3 text-sky-600 ring-1 ring-sky-200 dark:bg-sky-500/10 dark:text-sky-300 dark:ring-sky-400/20">
                <FlaskConical className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-lg font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-xl">
                    Unit Test Creator
                  </h1>
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-700 dark:bg-amber-500/10 dark:text-amber-200">
                    <Sparkles className="h-3 w-3" />
                    Multi-agent flow
                  </span>
                </div>
                {/* <p className="max-w-2xl text-[12px] leading-5 text-slate-500 dark:text-slate-400 sm:text-[13px]">
                  Paste a function, choose the language, and generate test files through a four-step agent pipeline with a cleaner, faster UI.
                </p> */}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                Responsive
              </span>
              <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                Theme ready
              </span> */}
              <button
                type="button"
                onClick={toggleTheme}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-[11px] font-semibold text-slate-600 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-300 hover:text-sky-700 hover:shadow-md dark:border-slate-600/40 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-sky-500/40 dark:hover:text-sky-300"
              >
                {theme === "light" ? <MoonStar className="h-3.5 w-3.5" /> : <SunMedium className="h-3.5 w-3.5" />}
                {theme === "light" ? "Dark mode" : "Light mode"}
              </button>
            </div>
          </div>
        </header>

        <main className="grid flex-1 gap-4 p-3 sm:gap-5 sm:p-5 xl:grid-cols-[minmax(0,1.03fr)_minmax(0,0.97fr)]">
          <section className="flex min-h-[420px] flex-col gap-4 rounded-[24px] border border-sky-100/80 bg-white/75 p-4 shadow-[0_18px_60px_rgba(14,165,233,0.08)] transition hover:shadow-[0_24px_80px_rgba(14,165,233,0.12)] dark:border-slate-700/40 dark:bg-slate-900/70 dark:shadow-[0_20px_70px_rgba(2,6,23,0.35)] sm:p-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">Source code</h2>
                {/* <p className="mt-1 text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                  Use one function or class for cleaner test generation. Text stays compact so the editor remains the focus.
                </p> */}
              </div>
              <div className="shrink-0">
                <LanguageSelector value={language} onChange={handleLanguageChange} />
              </div>
            </div>

            <CodeEditor code={code} language={language} onChange={setCode} theme={theme} />

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              {/* <p className="text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                Python, JavaScript, and TypeScript are supported. Output stays copy-ready in the right panel.
              </p> */}
              <button
                type="button"
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-sky-600 px-4 py-3 text-xs font-semibold text-white shadow-[0_16px_40px_rgba(2,132,199,0.28)] transition hover:-translate-y-0.5 hover:bg-sky-500 hover:shadow-[0_22px_44px_rgba(2,132,199,0.36)] disabled:cursor-not-allowed disabled:opacity-60 dark:bg-sky-500 dark:hover:bg-sky-400"
                onClick={handleGenerate}
                disabled={isLoading || !code.trim()}
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Generating
                  </>
                ) : (
                  <>
                    <FlaskConical size={16} />
                    Generate tests
                  </>
                )}
              </button>
            </div>

            {error && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-[11px] leading-5 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
                {error}
              </div>
            )}
          </section>

          <section className="flex min-h-[420px] flex-col gap-4 rounded-[24px] border border-slate-200/80 bg-white/78 p-4 shadow-[0_18px_60px_rgba(15,23,42,0.08)] transition hover:shadow-[0_24px_80px_rgba(15,23,42,0.12)] dark:border-slate-700/40 dark:bg-slate-900/74 dark:shadow-[0_20px_70px_rgba(2,6,23,0.4)] sm:p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">Generated output</h2>
                {/* <p className="mt-1 text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                  Track the pipeline, review cases, and switch between skeleton and final tests.
                </p> */}
              </div>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                Live panel
              </span>
            </div>

            {result ? (
                <TestOutput
                  finalTests={result.final_tests}
                  testCode={result.test_code}
                  testCases={result.test_cases}
                  language={result.language}
                  framework={result.framework}
                  theme={theme}
                />
            ) : isLoading ? (
              <div className="flex flex-1 flex-col items-center justify-center rounded-[22px] border border-sky-200/60 bg-gradient-to-br from-white via-sky-50/30 to-blue-50/40 p-10 backdrop-blur-sm dark:border-sky-500/20 dark:bg-gradient-to-br dark:from-slate-900/95 dark:via-slate-900/90 dark:to-sky-950/60">
                {/* Floating particles animation */}
                <div className="relative mb-4 h-32 w-64">
                  {/* Central glow */}
                  <div className="absolute left-1/2 top-1/2 h-20 w-20 -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-gradient-to-r from-sky-400/20 to-blue-400/20 blur-2xl"></div>
                  
                  {/* Animated particles */}
                  <div className="absolute left-[20%] top-[30%] h-3 w-3 animate-float rounded-full bg-purple-400/50 opacity-60 blur-sm [animation-delay:0s] [animation-duration:3s]"></div>
                  <div className="absolute left-[75%] top-[25%] h-2 w-2 animate-float rounded-full bg-blue-400/50 opacity-50 blur-sm [animation-delay:0.5s] [animation-duration:3.5s]"></div>
                  <div className="absolute left-[45%] top-[15%] h-2.5 w-2.5 animate-float rounded-full bg-emerald-400/50 opacity-55 blur-sm [animation-delay:1s] [animation-duration:4s]"></div>
                  <div className="absolute left-[60%] top-[65%] h-2 w-2 animate-float rounded-full bg-amber-400/50 opacity-45 blur-sm [animation-delay:1.5s] [animation-duration:3.8s]"></div>
                  <div className="absolute left-[30%] top-[70%] h-3 w-3 animate-float rounded-full bg-sky-400/50 opacity-60 blur-sm [animation-delay:0.8s] [animation-duration:3.2s]"></div>
                  <div className="absolute left-[85%] top-[55%] h-2 w-2 animate-float rounded-full bg-violet-400/50 opacity-50 blur-sm [animation-delay:2s] [animation-duration:3.6s]"></div>
                  
                  {/* Current agent icon - only one visible at a time */}
                  <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
                    {(() => {
                      const agents = [
                        { icon: Sparkles, label: 'Analyzing Code', color: 'bg-purple-500 shadow-purple-500/40' },
                        { icon: FlaskConical, label: 'Generating Test Cases', color: 'bg-sky-500 shadow-sky-500/40' },
                        { icon: Code, label: 'Writing Test Code', color: 'bg-blue-500 shadow-blue-500/40' },
                        { icon: CheckCheck, label: 'Adding Assertions', color: 'bg-emerald-500 shadow-emerald-500/40' }
                      ];
                      const current = agents[loadingStep];
                      const AgentIcon = current.icon;
                      
                      return (
                        <div 
                          key={loadingStep}
                          className={`animate-fade-scale rounded-lg p-3 shadow-lg ${current.color}`}
                        >
                          <AgentIcon className="h-6 w-6 text-white" strokeWidth={2.5} />
                        </div>
                      );
                    })()}
                  </div>
                </div>
                
                {/* Status text */}
                <div className="text-center">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                    {['Analyzing Code', 'Generating Test Cases', 'Writing Test Code', 'Adding Assertions'][loadingStep]}
                  </h3>
                  <p className="mt-1 text-[11px] text-slate-600 dark:text-slate-400">
                    Generation in progress...
                  </p>
                  
                  {/* Dynamic progress bar - more visible */}
                  <div className="mx-auto mt-4 h-1.5 w-48 overflow-hidden rounded-full bg-slate-200 shadow-inner dark:bg-slate-700">
                    <div 
                      className="h-full bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 shadow-lg transition-all duration-700 ease-out"
                      style={{ width: `${Math.min(((maxLoadingStep + 1) / 4) * 100, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-1 items-center justify-center rounded-[22px] border border-dashed border-slate-300 bg-slate-50/75 p-6 text-center dark:border-slate-700/40 dark:bg-slate-950/50">
                <div className="max-w-sm space-y-3">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-100 text-sky-600 dark:bg-sky-500/10 dark:text-sky-300">
                    <FlaskConical className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Ready when you are</p>
                    <p className="mt-1 text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                      Generate tests to populate this panel with pipeline status, categorized cases, and final output.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
