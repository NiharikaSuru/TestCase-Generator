import { CheckCircle, Circle, Loader2, XCircle, Sparkles, Beaker, Code, CheckCheck } from "lucide-react";
import type { AgentStep } from "../api/client";

const AGENT_CONFIG = [
  { name: "Code Analyzer", icon: Sparkles, color: "text-purple-500" },
  { name: "Test Case Generator", icon: Beaker, color: "text-blue-500" },
  { name: "Test Code Writer", icon: Code, color: "text-emerald-500" },
  { name: "Assertion Agent", icon: CheckCheck, color: "text-amber-500" },
];

interface Props {
  steps: AgentStep[];
  isLoading: boolean;
}

export default function AgentProgressStepper({ steps, isLoading }: Props) {
  return (
    <div className="relative space-y-4 py-2">
      {/* Vertical connecting line */}
      <div className="absolute left-[23px] top-8 h-[calc(100%-64px)] w-0.5 bg-gradient-to-b from-sky-300 via-blue-300 to-transparent dark:from-sky-500/40 dark:via-blue-500/30 dark:to-transparent"></div>
      
      {AGENT_CONFIG.map((agent, idx) => {
        const done = steps.find((s) => s.agent === agent.name);
        const isActive = isLoading && !done && steps.length === idx;
        const isPending = !done && !isActive;
        const AgentIcon = agent.icon;

        return (
          <div
            key={agent.name}
            className={`relative flex items-start gap-5 transition-all duration-300 ${
              isActive ? "scale-[1.02]" : "scale-100"
            }`}
          >
            {/* Icon container */}
            <div className="relative z-10 flex h-12 w-12 shrink-0 items-center justify-center">
              {done ? (
                done.status === "completed" ? (
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-emerald-100 to-emerald-50 shadow-md ring-4 ring-emerald-50 dark:from-emerald-500/25 dark:to-emerald-500/15 dark:shadow-emerald-500/20 dark:ring-emerald-500/10">
                    <CheckCircle size={24} className="text-emerald-600 dark:text-emerald-400" strokeWidth={2.5} />
                  </div>
                ) : (
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-rose-100 to-rose-50 shadow-md ring-4 ring-rose-50 dark:from-rose-500/25 dark:to-rose-500/15 dark:shadow-rose-500/20 dark:ring-rose-500/10">
                    <XCircle size={24} className="text-rose-600 dark:text-rose-400" strokeWidth={2.5} />
                  </div>
                )
              ) : isActive ? (
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-sky-100 to-blue-100 shadow-lg ring-4 ring-sky-50 dark:from-sky-500/30 dark:to-blue-500/25 dark:shadow-sky-500/30 dark:ring-sky-500/15">
                  <Loader2 size={24} className="animate-spin text-sky-600 dark:text-sky-300" strokeWidth={2.5} />
                </div>
              ) : (
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 ring-4 ring-slate-50 dark:bg-slate-800/60 dark:ring-slate-800/40">
                  <Circle size={24} className="text-slate-300 dark:text-slate-600" strokeWidth={2} />
                </div>
              )}
            </div>

            {/* Content */}
            <div className="min-w-0 flex-1 pt-2">
              <div className="flex items-center gap-2.5">
                <AgentIcon size={18} className={`${agent.color} ${isPending ? "opacity-30" : "opacity-100"}`} strokeWidth={2} />
                <h4 className={`text-[15px] font-semibold transition-colors ${
                  isPending 
                    ? "text-slate-400 dark:text-slate-600" 
                    : "text-slate-900 dark:text-slate-100"
                }`}>
                  {agent.name}
                </h4>
                {done && done.status === "completed" && (
                  <span className="ml-auto text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                    ✓ Done
                  </span>
                )}
              </div>
              
              {done && (
                <p className={`mt-2 text-[13px] leading-relaxed transition-all duration-300 ${
                  done.status === "completed" 
                    ? "text-slate-600 dark:text-slate-400" 
                    : "text-rose-600 dark:text-rose-400"
                }`}>
                  {done.output_summary}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
