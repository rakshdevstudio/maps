import { useEffect, useState } from "react";

import { useScraper } from "@/hooks/useScraper";
import { setApiBaseUrl } from "@/services/api";

const DEFAULT_FORM = {
  max_results_per_keyword: 20,
  delay_between_requests_ms: 1500,
  parallel_workers: 1,
  proxy_url: "",
  google_sheets_enabled: false,
  google_sheets_sheet_name: "MapsScraperResults",
  api_endpoint: "http://localhost:8000",
};

function Field({ label, hint, children }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-3">
        <h3 className="text-base font-semibold text-white">{label}</h3>
        <p className="mt-1 text-sm text-slate-400">{hint}</p>
      </div>
      {children}
    </div>
  );
}

export default function Settings() {
  const { settings, saveSettings, clearAllData } = useScraper();
  const [form, setForm] = useState(DEFAULT_FORM);
  const [saving, setSaving] = useState(false);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    if (settings) {
      setForm((current) => ({ ...current, ...settings }));
    }
  }, [settings]);

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        ...settings, // preserve existing hidden settings
        ...form,
        max_results_per_keyword: Number(form.max_results_per_keyword),
        delay_between_requests_ms: Number(form.delay_between_requests_ms),
        parallel_workers: Number(form.parallel_workers),
      };
      await saveSettings(payload);
      if (form.api_endpoint) setApiBaseUrl(form.api_endpoint);
    } finally {
      setSaving(false);
    }
  };

  const handleClearAllData = async () => {
    const confirmed = window.confirm(
      "Clear all data? This will stop the scraper, clear queue and results, reset statuses, and restart queue manager."
    );
    if (!confirmed) return;
    setClearing(true);
    try {
      await clearAllData();
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">Settings</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Scraper Configuration</h2>
        <p className="mt-3 max-w-3xl text-sm text-slate-400">
          Tune throughput and persistence settings.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Field label="Execution limits" hint="Control how many businesses are collected per keyword and how quickly requests fire.">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm text-slate-300">
              Max results per keyword
              <input type="number" min="1" max="200" value={form.max_results_per_keyword} onChange={(e) => updateField("max_results_per_keyword", e.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none" />
            </label>
            <label className="text-sm text-slate-300">
              Delay between requests (ms)
              <input type="number" min="0" value={form.delay_between_requests_ms} onChange={(e) => updateField("delay_between_requests_ms", e.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none" />
            </label>
            <label className="text-sm text-slate-300">
              Parallel workers
              <input type="number" min="1" max="10" value={form.parallel_workers} onChange={(e) => updateField("parallel_workers", e.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none" />
            </label>
            <label className="text-sm text-slate-300">
              Proxy URL
              <input value={form.proxy_url} onChange={(e) => updateField("proxy_url", e.target.value)} placeholder="http://user:pass@host:port" className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none placeholder:text-slate-500" />
            </label>
          </div>
        </Field>

        <Field label="Persistence" hint="Optionally stream each row to Google Sheets.">
          <div className="space-y-4">
            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
              Google Sheets integration
              <input type="checkbox" checked={form.google_sheets_enabled} onChange={(e) => updateField("google_sheets_enabled", e.target.checked)} className="h-4 w-4" />
            </label>
            <label className="text-sm text-slate-300">
              Google Sheets document name
              <input value={form.google_sheets_sheet_name} onChange={(e) => updateField("google_sheets_sheet_name", e.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none" />
            </label>
          </div>
        </Field>
      </div>

      <div className="flex flex-wrap justify-end gap-3">
        <button onClick={handleClearAllData} disabled={clearing} className="rounded-2xl border border-rose-400/30 bg-rose-500/20 px-5 py-3 text-sm font-semibold text-rose-100 transition hover:bg-rose-500/30 disabled:cursor-not-allowed disabled:opacity-50">
          {clearing ? "Clearing..." : "Clear All Data"}
        </button>
        <button onClick={handleSave} disabled={saving || clearing} className="rounded-2xl bg-cyan-500/90 px-5 py-3 text-sm font-semibold text-white transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50">
          {saving ? "Saving..." : "Save settings"}
        </button>
      </div>
    </div>
  );
}
