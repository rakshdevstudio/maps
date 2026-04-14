import { Pause, Play, RotateCcw, Square } from "lucide-react";


function ActionButton({ onClick, disabled, tone, icon: Icon, children }) {
  const toneClass =
    tone === "green"
      ? "bg-emerald-500/90 hover:bg-emerald-400"
      : tone === "amber"
        ? "bg-amber-500/90 hover:bg-amber-400"
        : tone === "red"
          ? "bg-rose-500/90 hover:bg-rose-400"
          : "bg-slate-700 hover:bg-slate-600";

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold text-white transition ${
        disabled ? "cursor-not-allowed bg-slate-800/70 text-slate-500" : toneClass
      }`}
    >
      <Icon className="h-4 w-4" />
      {children}
    </button>
  );
}


export default function ControlPanel({
  status,
  currentKeyword,
  activeWorkers,
  busyAction,
  onControl,
}) {
  const isRunning = status === "running";
  const isPaused = status === "paused";
  const canStart = ["idle", "stopped", "completed", "error"].includes(status);

  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">
            Queue Control
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-white">
            Live job orchestration
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            {currentKeyword
              ? `Currently processing: ${currentKeyword}`
              : "Ready to process queued search terms."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <ActionButton
            onClick={() => onControl("start")}
            disabled={!canStart || busyAction === "start"}
            tone="green"
            icon={Play}
          >
            Start
          </ActionButton>
          <ActionButton
            onClick={() => onControl(isPaused ? "resume" : "pause")}
            disabled={!isRunning && !isPaused}
            tone="amber"
            icon={isPaused ? RotateCcw : Pause}
          >
            {isPaused ? "Resume" : "Pause"}
          </ActionButton>
          <ActionButton
            onClick={() => onControl("stop")}
            disabled={canStart || busyAction === "stop"}
            tone="red"
            icon={Square}
          >
            Stop
          </ActionButton>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3 text-sm">
        <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-cyan-200">
          Status: {status}
        </span>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-slate-300">
          Active workers: {activeWorkers ?? 0}
        </span>
      </div>
    </div>
  );
}
