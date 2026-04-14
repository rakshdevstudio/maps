import { useEffect, useRef } from "react";
import { ScrollText } from "lucide-react";


const LEVEL_STYLES = {
  INFO: "text-cyan-300",
  WARNING: "text-amber-300",
  ERROR: "text-rose-300",
  DEBUG: "text-slate-400",
};


export default function LogsPanel({ logs }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/60 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
      <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-cyan-400/10 p-2">
            <ScrollText className="h-5 w-5 text-cyan-300" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Live execution logs</h3>
            <p className="text-sm text-slate-400">
              Every scraper step, retry, and save is streamed here.
            </p>
          </div>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
          Auto-scroll
        </span>
      </div>

      <div
        ref={scrollRef}
        className="h-[26rem] space-y-2 overflow-y-auto bg-slate-950/90 px-6 py-4 font-mono text-sm"
      >
        {(logs || []).length > 0 ? (
          logs.map((log) => (
            <div
              key={log.id ?? `${log.timestamp}-${log.message}`}
              className="rounded-2xl border border-white/5 bg-white/[0.03] px-3 py-2"
            >
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-500">
                  {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "--"}
                </span>
                <span className={LEVEL_STYLES[log.level] || "text-slate-300"}>
                  {log.level}
                </span>
              </div>
              <p className="mt-1 break-words text-slate-200">{log.message}</p>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-white/10 px-4 py-10 text-center text-slate-500">
            No logs yet. Start the scraper to stream activity.
          </div>
        )}
      </div>
    </div>
  );
}
