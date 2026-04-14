import { useCallback, useState } from "react";
import { toast } from "sonner";

import {
  getKeywords,
  resetAllKeywords,
  resetFailedKeywords,
  resetSkippedKeywords,
  uploadKeywords,
} from "@/services/api";


export function useKeywords() {
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 100,
    total: 0,
    total_pages: 1,
  });

  const fetchKeywords = useCallback(async (page = 1, limit = 100, status = "") => {
    setLoading(true);
    try {
      const data = await getKeywords(page, limit, status);
      setKeywords(data.items || []);
      setPagination({
        page: data.page,
        limit: data.limit,
        total: data.total,
        total_pages: data.total_pages,
      });
    } catch (error) {
      toast.error("Failed to load keyword queue");
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadFile = async (file, mode = "add") => {
    try {
      const result = await uploadKeywords(file, mode);
      toast.success(result.message);
      await fetchKeywords(1, pagination.limit);
      return result;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Upload failed");
      throw error;
    }
  };

  const resetFailed = async () => {
    const result = await resetFailedKeywords();
    toast.success(result.message);
    await fetchKeywords(pagination.page, pagination.limit);
    return result;
  };

  const resetSkipped = async () => {
    const result = await resetSkippedKeywords();
    toast.success(result.message);
    await fetchKeywords(pagination.page, pagination.limit);
    return result;
  };

  const resetAll = async () => {
    const result = await resetAllKeywords();
    toast.success(result.message);
    await fetchKeywords(pagination.page, pagination.limit);
    return result;
  };

  return {
    keywords,
    loading,
    pagination,
    fetchKeywords,
    uploadFile,
    resetFailed,
    resetSkipped,
    resetAll,
  };
}
