import { useEffect, useState } from "react";
import { toast } from "sonner";

import {
  adminResetAll,
  controlScraper,
  createBulkKeywords,
  getDashboardSnapshot,
  getSettings,
  getResultsStats,
  startBulkScrape,
  updateSettings,
  uploadKeywords as uploadKeywordsFile,
} from "@/services/api";


const EMPTY_SNAPSHOT = {
  status: "idle",
  current_keyword: null,
  active_workers: 0,
  totals: {
    total: 0,
    done: 0,
    pending: 0,
    processing: 0,
    failed: 0,
    skipped: 0,
    throttled: 0,
    results: 0,
    results_per_min: 0,
    success_rate: 0,
  },
  logs: [],
  keywords: [],
  keyword_progress: [],
  data_saver: null,
  last_error: null,
};


export function useScraper(intervalMs = 1500) {
  const [snapshot, setSnapshot] = useState(EMPTY_SNAPSHOT);
  const [settings, setSettings] = useState(null);
  const [resultsStats, setResultsStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState(null);

  const refreshSnapshot = async () => {
    const data = await getDashboardSnapshot();
    setSnapshot(data);
    return data;
  };

  const refreshSettings = async () => {
    const data = await getSettings();
    setSettings(data);
    return data;
  };

  const refreshResultsStats = async () => {
    const data = await getResultsStats();
    setResultsStats(data);
    return data;
  };

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [snapshotData, settingsData, statsData] = await Promise.all([
          getDashboardSnapshot(),
          getSettings(),
          getResultsStats(),
        ]);
        if (cancelled) {
          return;
        }
        setSnapshot(snapshotData);
        setSettings(settingsData);
        setResultsStats(statsData);
      } catch (error) {
        if (!cancelled) {
          toast.error("Unable to reach backend API");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    load();
    const intervalId = setInterval(async () => {
      try {
        const data = await getDashboardSnapshot();
        if (!cancelled) {
          setSnapshot(data);
        }
      } catch {
        // Keep the last known snapshot visible.
      }
    }, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [intervalMs]);

  const runControl = async (action) => {
    try {
      setBusyAction(action);
      const data = await controlScraper(action);
      setSnapshot((current) => ({ ...current, ...data }));
      toast.success(`Scraper ${action} command sent`);
    } catch (error) {
      toast.error(error.response?.data?.detail || `Failed to ${action} scraper`);
    } finally {
      setBusyAction(null);
    }
  };

  const addBulkKeywords = async (keywordsText, mode = "add") => {
    try {
      if (mode === "replace") {
        await adminResetAll();
      }
      const result = await createBulkKeywords({
        keywords_text: keywordsText,
        mode,
      });
      toast.success(result.message);
      await refreshSnapshot();
      return result;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add keywords");
      throw error;
    }
  };

  const uploadKeywords = async (file, mode = "add") => {
    try {
      if (mode === "replace") {
        await adminResetAll();
      }
      const result = await uploadKeywordsFile(file, mode);
      toast.success(result.message);
      await refreshSnapshot();
      return result;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Upload failed");
      throw error;
    }
  };

  const addAndStart = async (keywordsText, mode = "add") => {
    try {
      setBusyAction("start");
      if (mode === "replace") {
        await adminResetAll();
      }
      const data = await startBulkScrape({
        keywords_text: keywordsText,
        mode,
      });
      setSnapshot((current) => ({ ...current, ...data }));
      toast.success("Queue updated and scraper started");
      return data;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to start queue");
      throw error;
    } finally {
      setBusyAction(null);
    }
  };

  const saveSettings = async (nextSettings) => {
    try {
      const data = await updateSettings(nextSettings);
      setSettings(data);
      toast.success("Settings saved");
      return data;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save settings");
      throw error;
    }
  };

  const clearAllData = async () => {
    try {
      const result = await adminResetAll();
      await Promise.all([refreshSnapshot(), refreshSettings(), refreshResultsStats()]);
      toast.success(result.message || "All data cleared");
      return result;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to clear all data");
      throw error;
    }
  };

  return {
    snapshot,
    settings,
    resultsStats,
    loading,
    busyAction,
    refreshSnapshot,
    refreshSettings,
    refreshResultsStats,
    runControl,
    addBulkKeywords,
    uploadKeywords,
    addAndStart,
    saveSettings,
    clearAllData,
  };
}
