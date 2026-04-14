import axios from "axios";
import { toast } from "sonner";


const STORAGE_KEY = "mapscraper_api_base_url";


function resolveApiBaseUrl() {
  if (typeof window !== "undefined") {
    return (
      window.localStorage.getItem(STORAGE_KEY) ||
      import.meta.env.VITE_API_BASE_URL ||
      "http://localhost:8000"
    );
  }
  return import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
}


const API = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 60000,
});


export function setApiBaseUrl(url) {
  const normalized = (url || "").trim() || "http://localhost:8000";
  API.defaults.baseURL = normalized;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, normalized);
  }
}


API.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Unexpected API error";
    if (error.response?.status >= 500) {
      toast.error(message);
    }
    return Promise.reject(error);
  },
);


export async function getDashboardSnapshot() {
  const response = await API.get("/dashboard/snapshot");
  return response.data;
}


export async function getScraperStatus() {
  const response = await API.get("/status");
  return response.data;
}


export async function getMetrics() {
  const response = await API.get("/metrics");
  return response.data;
}


export async function getLogs(limit = 100) {
  const response = await API.get("/logs", { params: { limit } });
  return response.data;
}


export async function controlScraper(action) {
  const response = await API.post(`/control/${action}`);
  return response.data;
}


export async function getKeywords(page = 1, limit = 100, status = "") {
  const response = await API.get("/keywords", {
    params: {
      page,
      limit,
      ...(status ? { status } : {}),
    },
  });
  return response.data;
}


export async function getKeywordProgress(page = 1, limit = 100, search = "", status = "") {
  const response = await API.get("/keywords/progress", {
    params: {
      page,
      limit,
      ...(search ? { search } : {}),
      ...(status ? { status } : {}),
    },
  });
  return response.data;
}


export async function createBulkKeywords(payload) {
  const response = await API.post("/keywords/bulk", payload);
  return response.data;
}


export async function startBulkScrape(payload) {
  const response = await API.post("/api/scrape", payload);
  return response.data;
}


export async function adminResetAll() {
  const response = await API.post("/admin/reset-all");
  return response.data;
}


export async function uploadKeywords(file, mode = "add") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", mode);
  const response = await API.post("/keywords/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}


export async function resetFailedKeywords() {
  const response = await API.post("/keywords/reset-failed");
  return response.data;
}


export async function resetSkippedKeywords() {
  const response = await API.post("/keywords/reset-skipped");
  return response.data;
}


export async function resetAllKeywords() {
  const response = await API.post("/keywords/reset-all");
  return response.data;
}


export async function getSettings() {
  const response = await API.get("/settings");
  return response.data;
}


export async function updateSettings(settings) {
  const response = await API.put("/settings", settings);
  return response.data;
}


export async function getResultsStats() {
  const response = await API.get("/results/stats");
  return response.data;
}


export async function getResults(params = {}) {
  const response = await API.get("/results", { params });
  return response.data;
}


export async function exportResultsCsv(params = {}) {
  const response = await API.get("/results/export", {
    params,
    responseType: "blob",
  });
  return response.data;
}


export default API;
