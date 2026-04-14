import { Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { useKeywords } from "@/hooks/useKeywords";
import { useScraper } from "@/hooks/useScraper";


function statusTone(status) {
  const normalized = (status || "").toLowerCase();
  if (normalized === "done") return "text-emerald-300";
  if (normalized === "processing") return "text-cyan-300";
  if (normalized === "failed" || normalized === "throttled") return "text-rose-300";
  if (normalized === "skipped") return "text-amber-300";
  return "text-slate-300";
}


export default function Keywords() {
  const { snapshot, addBulkKeywords, addAndStart, uploadKeywords } = useScraper();
  const { keywords, pagination, loading, fetchKeywords } = useKeywords();
  const [bulkText, setBulkText] = useState("");
  const [uploadMode, setUploadMode] = useState("add");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchKeywords(page, 25, statusFilter);
  }, [fetchKeywords, page, statusFilter]);

  const queuedCount = useMemo(
    () =>
      bulkText
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean).length,
    [bulkText],
  );

  const submitBulk = async (shouldStart) => {
    if (!bulkText.trim()) {
      return;
    }
    if (shouldStart) {
      await addAndStart(bulkText, uploadMode);
    } else {
      await addBulkKeywords(bulkText, uploadMode);
    }
    setBulkText("");
    setPage(1);
    await fetchKeywords(1, 25, statusFilter);
  };

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    await uploadKeywords(file, uploadMode);
    event.target.value = "";
    setPage(1);
    await fetchKeywords(1, 25, statusFilter);
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">
          Keyword Intake
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-white">
          Bulk queue management
        </h2>
        <p className="mt-3 max-w-3xl text-sm text-slate-400">
          Paste unlimited search terms, stage them in the queue, or enqueue and launch
          the scraper in one action.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-xl font-semibold text-white">Bulk keyword input</h3>
              <p className="mt-1 text-sm text-slate-400">
                One keyword per line. This queue survives refreshes and resumes.
              </p>
            </div>
            <select
              value={uploadMode}
              onChange={(event) => setUploadMode(event.target.value)}
              className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 outline-none"
            >
              <option value="add">Add new only</option>
              <option value="sync">Sync and reset matching rows</option>
              <option value="replace">Replace the full queue</option>
            </select>
          </div>

          <textarea
            value={bulkText}
            onChange={(event) => setBulkText(event.target.value)}
            placeholder={"restaurants in bangalore\ndentists in london\nreal estate agents in dubai"}
            className="mt-5 h-80 w-full rounded-3xl border border-white/10 bg-slate-950/90 px-5 py-4 text-sm text-white outline-none placeholder:text-slate-500"
          />

          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-400">
              {queuedCount} keywords ready to queue
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => submitBulk(false)}
                disabled={!bulkText.trim()}
                className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Add to queue
              </button>
              <button
                onClick={() => submitBulk(true)}
                disabled={!bulkText.trim()}
                className="rounded-2xl bg-emerald-500/90 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Add and start
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
          <h3 className="text-xl font-semibold text-white">Queue summary</h3>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm text-slate-400">Status</p>
              <p className="mt-2 text-2xl font-semibold text-white">{snapshot.status}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm text-slate-400">Running keyword</p>
              <p className="mt-2 text-sm text-white">
                {snapshot.current_keyword || "Waiting"}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm text-slate-400">Saved businesses</p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {snapshot.totals.results}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm text-slate-400">Duplicates skipped</p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {snapshot.data_saver?.duplicate_count ?? 0}
              </p>
            </div>
          </div>

          <label className="mt-6 flex cursor-pointer items-center justify-center gap-2 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15">
            <Upload className="h-4 w-4" />
            Import file (.csv, .xlsx, .txt)
            <input
              type="file"
              className="hidden"
              accept=".csv,.xlsx,.xls,.txt"
              onChange={handleUpload}
            />
          </label>
        </div>
      </div>

      <div className="rounded-3xl border border-white/10 bg-slate-950/60 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
        <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-xl font-semibold text-white">Keyword queue</h3>
            <p className="mt-1 text-sm text-slate-400">
              Inspect status across the full queue and watch rows update live.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <select
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value);
                setPage(1);
              }}
              className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 outline-none"
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="done">Done</option>
              <option value="failed">Failed</option>
              <option value="throttled">Throttled</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-white/10 text-xs uppercase tracking-[0.18em] text-slate-500">
              <tr>
                <th className="px-6 py-4">Keyword</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Updated</th>
              </tr>
            </thead>
            <tbody>
              {keywords.map((keyword) => (
                <tr key={keyword.id} className="border-b border-white/5">
                  <td className="px-6 py-4 text-slate-100">{keyword.text}</td>
                  <td className={`px-6 py-4 font-medium ${statusTone(keyword.status)}`}>
                    {keyword.status}
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {keyword.updated_at
                      ? new Date(keyword.updated_at).toLocaleString()
                      : "--"}
                  </td>
                </tr>
              ))}
              {!loading && keywords.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-10 text-center text-slate-500">
                    No keywords matched the current filter.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between px-6 py-4 text-sm text-slate-400">
          <span>
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={pagination.page <= 1}
              className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 transition hover:bg-white/10 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() =>
                setPage((current) => Math.min(pagination.total_pages, current + 1))
              }
              disabled={pagination.page >= pagination.total_pages}
              className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 transition hover:bg-white/10 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
