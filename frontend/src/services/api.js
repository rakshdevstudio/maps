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


export async function promoteToLead(businessId) {
  const response = await API.post("/leads/promote", { business_id: businessId });
  return response.data;
}


export async function getLeads(params = {}) {
  const response = await API.get("/leads", { params });
  return response.data;
}


export async function getLeadStats() {
  const response = await API.get("/leads/stats");
  return response.data;
}


export async function getLead(leadId) {
  const response = await API.get(`/leads/${leadId}`);
  return response.data;
}


export async function updateLead(leadId, data) {
  const response = await API.patch(`/leads/${leadId}`, data);
  return response.data;
}


export async function deleteLead(leadId) {
  const response = await API.delete(`/leads/${leadId}`);
  return response.data;
}


export async function getLeadActivities(leadId) {
  const response = await API.get(`/leads/${leadId}/activities`);
  return response.data;
}


export async function addLeadActivity(leadId, type, content = "") {
  const response = await API.post(`/leads/${leadId}/activities`, { type, content });
  return response.data;
}


export async function runAudit(leadId) {
  const response = await API.post(`/audits/lead/${leadId}`);
  return response.data;
}


export async function getAuditStats() {
  const response = await API.get("/audits/stats");
  return response.data;
}


export async function getCommandCenter(params = {}) {
  const response = await API.get("/leads/command-center", { params });
  return response.data;
}


export async function getPipelineRevenue() {
  const response = await API.get("/leads/pipeline-revenue");
  return response.data;
}


export async function getLeadOutreach(leadId) {
  const response = await API.get(`/leads/${leadId}/outreach`);
  return response.data;
}


export async function generateLeadOutreach(leadId) {
  const response = await API.post(`/leads/${leadId}/outreach`);
  return response.data;
}


export async function getTodayView() {
  const response = await API.get("/leads/today");
  return response.data;
}


export async function getPipelineForecast() {
  const response = await API.get("/leads/pipeline-revenue");
  return response.data;
}


export async function getProposalTemplates() {
  const response = await API.get("/proposals/templates");
  return response.data;
}


export async function generateProposal(leadId, payload) {
  const response = await API.post(`/proposals/generate/${leadId}`, payload);
  return response.data;
}


export async function getProposals(params = {}) {
  const response = await API.get("/proposals", { params });
  return response.data;
}


export async function getProposal(id) {
  const response = await API.get(`/proposals/${id}`);
  return response.data;
}


export async function sendProposal(id) {
  const response = await API.post(`/proposals/${id}/send`);
  return response.data;
}


export async function acceptProposal(id, payload) {
  const response = await API.post(`/proposals/${id}/accept`, payload);
  return response.data;
}


export async function rejectProposal(id, payload) {
  const response = await API.post(`/proposals/${id}/reject`, payload);
  return response.data;
}


export async function getProposalStats() {
  const response = await API.get("/proposals/stats");
  return response.data;
}


export async function getProposalNegotiation(id) {
  const response = await API.get(`/proposals/${id}/negotiation`);
  return response.data;
}


export function getProposalPdfUrl(id) {
  return `${API.defaults.baseURL}/proposals/${id}/pdf`;
}

// ── Phase 6A: Project Delivery API ───────────────────────────────

export async function getProjects(params = {}) {
  const response = await API.get("/projects", { params });
  return response.data;
}

export async function getProjectStats() {
  const response = await API.get("/projects/stats");
  return response.data;
}

export async function getProject(id) {
  const response = await API.get(`/projects/${id}`);
  return response.data;
}

export async function updateProject(id, data) {
  const response = await API.patch(`/projects/${id}`, data);
  return response.data;
}

export async function updateMilestone(projectId, milestoneId, data) {
  const response = await API.patch(`/projects/${projectId}/milestones/${milestoneId}`, data);
  return response.data;
}

export async function createTask(projectId, data) {
  const response = await API.post(`/projects/${projectId}/tasks`, data);
  return response.data;
}

export async function updateTask(projectId, taskId, data) {
  const response = await API.patch(`/projects/${projectId}/tasks/${taskId}`, data);
  return response.data;
}

export async function deleteTask(projectId, taskId) {
  const response = await API.delete(`/projects/${projectId}/tasks/${taskId}`);
  return response.data;
}

export async function uploadProjectFile(projectId, file, milestoneId = null, taskId = null) {
  const formData = new FormData();
  formData.append("file", file);
  if (milestoneId) formData.append("milestone_id", milestoneId);
  if (taskId) formData.append("task_id", taskId);
  
  const response = await API.post(`/projects/${projectId}/files`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function deleteProjectFile(fileId) {
  const response = await API.delete(`/projects/files/${fileId}`);
  return response.data;
}

export function getProjectFileUrl(fileId) {
  return `${API.defaults.baseURL}/projects/files/${fileId}/download`;
}

export async function getProjectTimeline(projectId) {
  const response = await API.get(`/projects/${projectId}/timeline`);
  return response.data;
}

export async function getProjectLifecycle(projectId) {
  const response = await API.get(`/projects/${projectId}/lifecycle`);
  return response.data;
}

export default API;
