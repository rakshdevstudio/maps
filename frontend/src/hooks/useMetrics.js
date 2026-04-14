import { useEffect, useState } from "react";

import { getMetrics } from "@/services/api";


export function useMetrics(intervalMs = 1500) {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchMetrics = async () => {
      try {
        const data = await getMetrics();
        if (!cancelled) {
          setMetrics(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
        }
      }
    };

    fetchMetrics();
    const intervalId = setInterval(fetchMetrics, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [intervalMs]);

  return { metrics, error };
}
