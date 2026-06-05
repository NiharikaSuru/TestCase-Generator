import { useState, useRef, useEffect } from "react";
import { ChevronDown, Check } from "lucide-react";

interface Props {
  value: "python" | "javascript" | "typescript";
  onChange: (value: "python" | "javascript" | "typescript") => void;
}

const LANGUAGES = [
  { value: "python", label: "Python", sublabel: "pytest" },
  { value: "javascript", label: "JavaScript", sublabel: "Jest" },
  { value: "typescript", label: "TypeScript", sublabel: "Jest" },
] as const;

export default function LanguageSelector({ value, onChange }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedLang = LANGUAGES.find((lang) => lang.value === value);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 shadow-sm transition hover:border-sky-300 hover:shadow-md dark:border-slate-700 dark:bg-slate-900 dark:hover:border-sky-500/40"
      >
        <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
          Language
        </span>
        <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-100">
          {selectedLang?.label}
        </span>
        <ChevronDown 
          className={`h-3.5 w-3.5 text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`} 
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-48 rounded-2xl border border-slate-200 bg-white p-1 shadow-xl dark:border-slate-700 dark:bg-slate-900">
          {LANGUAGES.map((lang) => {
            const isSelected = lang.value === value;
            return (
              <button
                key={lang.value}
                type="button"
                onClick={() => {
                  onChange(lang.value);
                  setIsOpen(false);
                }}
                className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left transition hover:bg-sky-50 dark:hover:bg-sky-500/10"
              >
                <div>
                  <div className="text-[11px] font-semibold text-slate-700 dark:text-slate-100">
                    {lang.label}
                  </div>
                  <div className="text-[10px] text-slate-500 dark:text-slate-400">
                    {lang.sublabel}
                  </div>
                </div>
                {isSelected && (
                  <Check className="h-4 w-4 text-sky-600 dark:text-sky-400" strokeWidth={2.5} />
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
