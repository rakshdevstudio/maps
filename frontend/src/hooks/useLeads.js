import { useCallback, useState } from "react";
import { toast } from "sonner";

import {
  addLeadActivity,
  deleteLead as deleteLeadApi,
  getLead,
  getLeadActivities,
  getLeads,
  getLeadStats,
  promoteToLead as promoteToLeadApi,
  updateLead as updateLeadApi,
} from "@/services/api";


export function useLeads() {
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState({
    new: 0,
    contacted: 0,
    interested: 0,
    not_interested: 0,
    closed_won: 0,
    closed_lost: 0,
  });
  const [pagination, setPagination] = useState({ page: 1, limit: 50, total: 0, total_pages: 1 });
  const [loading, setLoading] = useState(false);

  const fetchLeads = useCallback(async (page = 1, limit = 50, status = "", priority = null, search = "") => {
    setLoading(true);
    try {
      const data = await getLeads({ page, limit, status, priority, search });
      setLeads(data.items || []);
      setPagination({
        page: data.page,
        limit: data.limit,
        total: data.total,
        total_pages: data.total_pages,
      });
    } catch (error) {
      toast.error("Failed to load leads");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const data = await getLeadStats();
      setStats(data);
    } catch (error) {
      // Background fail is ok
    }
  }, []);

  const promoteToLead = async (businessId) => {
    try {
      const lead = await promoteToLeadApi(businessId);
      toast.success("Business added to pipeline");
      await fetchStats();
      return lead;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add to pipeline");
      throw error;
    }
  };

  const updateLead = async (leadId, data) => {
    try {
      const updated = await updateLeadApi(leadId, data);
      toast.success("Lead updated");
      setLeads((current) =>
        current.map((lead) => (lead.id === leadId ? { ...lead, ...updated } : lead))
      );
      await fetchStats();
      return updated;
    } catch (error) {
      toast.error("Failed to update lead");
      throw error;
    }
  };

  const deleteLead = async (leadId) => {
    try {
      await deleteLeadApi(leadId);
      toast.success("Lead removed from pipeline");
      setLeads((current) => current.filter((lead) => lead.id !== leadId));
      await fetchStats();
    } catch (error) {
      toast.error("Failed to delete lead");
      throw error;
    }
  };

  const fetchLeadDetails = async (leadId) => {
    try {
      const data = await getLead(leadId);
      return data;
    } catch (error) {
      toast.error("Failed to load lead details");
      throw error;
    }
  };

  const logActivity = async (leadId, type, content) => {
    try {
      const activity = await addLeadActivity(leadId, type, content);
      return activity;
    } catch (error) {
      toast.error("Failed to log activity");
      throw error;
    }
  };

  return {
    leads,
    stats,
    pagination,
    loading,
    fetchLeads,
    fetchStats,
    promoteToLead,
    updateLead,
    deleteLead,
    fetchLeadDetails,
    logActivity,
  };
}
