import { useEffect, useState } from "react";

import { useScraper } from "@/hooks/useScraper";
import { setApiBaseUrl } from "@/services/api";


const DEFAULT_FORM = {
  max_results_per_keyword: 20,
  delay_between_requests_ms: 1500,
  parallel_workers: 1,
  proxy_url: "",
  headless: true,
  auto_save: true,
  google_sheets_enabled: false,
  google_sheets_sheet_name: "MapsScraperResults",
  api_endpoint: "http://localhost:8000",
  max_retries: 3,
  page_timeout_ms: 45000,
  browser_executable_path: "",
  scroll_depth_limit: 12,
  stop_on_duplicate_results: true,
  duplicate_stop_threshold: 5,
  adaptive_delay_enabled: true,
  adaptive_delay_max_ms: 8000,
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
      setForm({ ...DEFAULT_FORM, ...settings });
    }
  }, [settings]);

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        ...form,
        max_results_per_keyword: Number(form.max_results_per_keyword),
        delay_between_requests_ms: Number(form.delay_between_requests_ms),
        parallel_workers: Number(form.parallel_workers),
        max_retries: Number(form.max_retries),
        page_timeout_ms: Number(form.page_timeout_ms),
        scroll_depth_limit: Number(form.scroll_depth_limit),
        duplicate_stop_threshold: Number(form.duplicate_stop_threshold),
        adaptive_delay_max_ms: Number(form.adaptive_delay_max_ms),
      };
      await saveSettings(payload);
      setApiBaseUrl(payload.api_endpoint);
    } finally {
      setSaving(false);
    }
  };

  const handleClearAllData = async () => {
    const confirmed = window.confirm(
      "Clear all data? This will stop the scraper, clear queue and results, reset statuses, and restart queue manager.",
    );
    if (!confirmed) {
      return;
    }

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
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">
          Settings
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-white">
          Scraper runtime configuration
        </h2>
        <p className="mt-3 max-w-3xl text-sm text-slate-400">
          Tune throughput, browser mode, persistence, and endpoint settings without
          editing code.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Field
          label="Execution limits"
          hint="Control how many businesses are collected per keyword and how quickly requests fire."
        >
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm text-slate-300">
              Max results per keyword
              <input
                type="number"
                min="1"
                max="200"
                value={form.max_results_per_keyword}
                onChange={(event) => updateField("max_results_per_keyword", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
            <label className="text-sm text-slate-300">
              Delay between requests (ms)
              <input
                type="number"
                min="0"
                value={form.delay_between_requests_ms}
                onChange={(event) => updateField("delay_between_requests_ms", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
            <label className="text-sm text-slate-300">
              Parallel workers
              <input
                type="number"
                min="1"
                max="10"
                value={form.parallel_workers}
                onChange={(event) => updateField("parallel_workers", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
            <label className="text-sm text-slate-300">
              Retry attempts
              <input
                type="number"
                min="1"
                max="10"
                value={form.max_retries}
                onChange={(event) => updateField("max_retries", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
          </div>
        </Field>

        <Field
          label="Browser and proxy"
          hint="Choose headless mode, override the browser executable, or route traffic through a proxy."
        >
          <div className="space-y-4">
            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
              Headless browser
              <input
                type="checkbox"
                checked={form.headless}
                onChange={(event) => updateField("headless", event.target.checked)}
                className="h-4 w-4"
              />
            </label>
            <label className="text-sm text-slate-300">
              Proxy URL
              <input
                value={form.proxy_url}
                onChange={(event) => updateField("proxy_url", event.target.value)}
                placeholder="http://user:pass@host:port"
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none placeholder:text-slate-500"
              />
            </label>
            <label className="text-sm text-slate-300">
              Browser executable path
              <input
                value={form.browser_executable_path}
                onChange={(event) => updateField("browser_executable_path", event.target.value)}
                placeholder="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none placeholder:text-slate-500"
              />
            </label>
            <label className="text-sm text-slate-300">
              Page timeout (ms)
              <input
                type="number"
                min="5000"
                value={form.page_timeout_ms}
                onChange={(event) => updateField("page_timeout_ms", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
            <label className="text-sm text-slate-300">
              Scroll depth limit
              <input
                type="number"
                min="1"
                max="100"
                value={form.scroll_depth_limit}
                onChange={(event) => updateField("scroll_depth_limit", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
              Stop on duplicate streak
              <input
                type="checkbox"
                checked={form.stop_on_duplicate_results}
                onChange={(event) => updateField("stop_on_duplicate_results", event.target.checked)}
                className="h-4 w-4"
              />
            </label>
            <label className="text-sm text-slate-300">
              Duplicate streak threshold
              <input
                type="number"
                min="1"
                max="50"
                value={form.duplicate_stop_threshold}
                onChange={(event) => updateField("duplicate_stop_threshold", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
              Adaptive delay when blocked
              <input
                type="checkbox"
                checked={form.adaptive_delay_enabled}
                onChange={(event) => updateField("adaptive_delay_enabled", event.target.checked)}
                className="h-4 w-4"
              />
            </label>
            <label className="text-sm text-slate-300">
              Adaptive delay max (ms)
              <input
                type="number"
                min="500"
                max="120000"
                value={form.adaptive_delay_max_ms}
                onChange={(event) => updateField("adaptive_delay_max_ms", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
          </div>
        </Field>

        <Field
          label="Persistence"
          hint="Save to disk continuously and optionally stream each row to Google Sheets."
        >
          <div className="space-y-4">
            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
              Auto-save local CSV
              <input
                type="checkbox"
                checked={form.auto_save}
                onChange={(event) => updateField("auto_save", event.target.checked)}
                className="h-4 w-4"
              />
            </label>
            <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
              Google Sheets integration
              <input
                type="checkbox"
                checked={form.google_sheets_enabled}
                onChange={(event) => updateField("google_sheets_enabled", event.target.checked)}
                className="h-4 w-4"
              />
            </label>
            <label className="text-sm text-slate-300">
              Google Sheets document name
              <input
                value={form.google_sheets_sheet_name}
                onChange={(event) => updateField("google_sheets_sheet_name", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
              />
            </label>
          </div>
        </Field>

        <Field
          label="API endpoint"
          hint="This value is stored in the browser and used by the frontend client for future requests."
        >
          <label className="text-sm text-slate-300">
            Backend API base URL
            <input
              value={form.api_endpoint}
              onChange={(event) => updateField("api_endpoint", event.target.value)}
              className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-white outline-none"
            />
          </label>
        </Field>
      </div>

      <div className="flex flex-wrap justify-end gap-3">
        <button
          onClick={handleClearAllData}
          disabled={clearing}
          className="rounded-2xl border border-rose-400/30 bg-rose-500/20 px-5 py-3 text-sm font-semibold text-rose-100 transition hover:bg-rose-500/30 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {clearing ? "Clearing..." : "Clear All Data"}
        </button>
        <button
          onClick={handleSave}
          disabled={saving || clearing}
          className="rounded-2xl bg-cyan-500/90 px-5 py-3 text-sm font-semibold text-white transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save settings"}
        </button>
      </div>
    </div>
  );
}
