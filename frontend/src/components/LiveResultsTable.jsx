import { Download, Search, Plus, Check } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { exportResultsCsv, getResults } from "@/services/api";
import { useLeads } from "@/hooks/useLeads";


function toCsvFilename(keyword) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  if (!keyword) {
    return `results_${timestamp}.csv`;
  }
  const safeKeyword = keyword.trim().replace(/\s+/g, "_").slice(0, 40);
  return `results_${safeKeyword}_${timestamp}.csv`;
}


function statusText(isLoading, isRefreshing) {
  if (isLoading) {
    return "Loading results...";
  }
  if (isRefreshing) {
    return "Refreshing";
  }
  return "Live";
}


export default function LiveResultsTable({ pollIntervalMs = 1500 }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [keyword, setKeyword] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const { promoteToLead } = useLeads();
  const [promoted, setPromoted] = useState(new Set());

  const params = useMemo(
    () => ({
      page,
      limit: 50,
      ...(search ? { search } : {}),
      ...(keyword ? { keyword } : {}),
      ...(category ? { category } : {}),
    }),
    [page, search, keyword, category],
  );

  useEffect(() => {
    let cancelled = false;

    const load = async (isFirstLoad) => {
      if (isFirstLoad) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      try {
        const data = await getResults(params);
        if (cancelled) {
          return;
        }
        setItems(data.items || []);
        setTotal(data.total || 0);
        setTotalPages(data.total_pages || 1);
      } finally {
        if (!cancelled) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    };

    load(true);
    const intervalId = setInterval(() => load(false), pollIntervalMs);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [params, pollIntervalMs]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportResultsCsv({
        ...(search ? { search } : {}),
        ...(keyword ? { keyword } : {}),
        ...(category ? { category } : {}),
      });

      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = toCsvFilename(keyword);
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/60 shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
      <div className="border-b border-white/10 px-6 py-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">Live Results</p>
            <h3 className="mt-2 text-xl font-semibold text-white">Businesses discovered in real time</h3>
            <p className="mt-1 text-sm text-slate-400">{total} rows saved</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
              {statusText(loading, refreshing)}
            </span>
            <button
              onClick={handleExport}
              disabled={exporting}
              className="inline-flex items-center gap-2 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-sm text-cyan-100 transition hover:bg-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Download className="h-4 w-4" />
              {exporting ? "Exporting..." : "Export CSV"}
            </button>
          </div>
        </div>

        <div className="mt-4 grid gap-3 lg:grid-cols-3">
          <label className="relative">
            <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
            <input
              value={search}
              onChange={(event) => {
                setPage(1);
                setSearch(event.target.value);
              }}
              placeholder="Search name, address, phone..."
              className="w-full rounded-2xl border border-white/10 bg-slate-950/90 py-3 pl-9 pr-3 text-sm text-white outline-none placeholder:text-slate-500"
            />
          </label>
          <input
            value={keyword}
            onChange={(event) => {
              setPage(1);
              setKeyword(event.target.value);
            }}
            placeholder="Filter keyword"
            className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-3 py-3 text-sm text-white outline-none placeholder:text-slate-500"
          />
          <input
            value={category}
            onChange={(event) => {
              setPage(1);
              setCategory(event.target.value);
            }}
            placeholder="Filter category"
            className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-3 py-3 text-sm text-white outline-none placeholder:text-slate-500"
          />
        </div>
      </div>

      <div className="max-h-[28rem] overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="sticky top-0 z-10 border-b border-white/10 bg-slate-950/95 text-xs uppercase tracking-[0.18em] text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Rating</th>
              <th className="px-4 py-3">Address</th>
              <th className="px-4 py-3">Phone</th>
              <th className="px-4 py-3">Website</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Keyword</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.id} className="border-b border-white/5">
                <td className="max-w-[14rem] px-4 py-3 text-slate-100">{row.name || "--"}</td>
                <td className="px-4 py-3 text-slate-300">{row.rating ?? "--"}</td>
                <td className="max-w-[18rem] px-4 py-3 text-slate-300">{row.address || "--"}</td>
                <td className="px-4 py-3 text-slate-300">{row.phone || "--"}</td>
                <td className="max-w-[15rem] px-4 py-3 text-cyan-200">
                  {row.website ? (
                    <a href={row.website} target="_blank" rel="noreferrer" className="underline decoration-cyan-300/40 underline-offset-2">
                      {row.website}
                    </a>
                  ) : (
                    "--"
                  )}
                </td>
                <td className="px-4 py-3 text-slate-300">{row.category || "--"}</td>
                <td className="max-w-[15rem] px-4 py-3 text-slate-300">{row.keyword || "--"}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={async () => {
                      try {
                        await promoteToLead(row.id);
                        setPromoted(new Set([...promoted, row.id]));
                      } catch (e) { }
                    }}
                    disabled={promoted.has(row.id)}
                    className="inline-flex items-center gap-1 whitespace-nowrap rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {promoted.has(row.id) ? (
                      <><Check className="h-3 w-3 text-emerald-400" /> In Pipeline</>
                    ) : (
                      <><Plus className="h-3 w-3 text-cyan-300" /> Add to Pipeline</>
                    )}
                  </button>
                </td>
              </tr>
            ))}
            {!loading && items.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-slate-500">
                  No results found with current filters.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-white/10 px-6 py-4 text-sm text-slate-400">
        <span>Page {page} of {totalPages}</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            disabled={page <= 1}
            className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 transition hover:bg-white/10 disabled:opacity-40"
          >
            Previous
          </button>
          <button
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            disabled={page >= totalPages}
            className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 transition hover:bg-white/10 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
