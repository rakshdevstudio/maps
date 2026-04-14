import { useEffect, useState } from "react";

import { getLogs } from "@/services/api";


export function useLogs(intervalMs = 1500, limit = 100) {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchLogs = async () => {
      try {
        const data = await getLogs(limit);
        if (!cancelled) {
          setLogs(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
        }
      }
    };

    fetchLogs();
    const intervalId = setInterval(fetchLogs, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [intervalMs, limit]);

  return { logs, error };
}
