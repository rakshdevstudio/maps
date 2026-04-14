import { useEffect, useState } from "react";

import { getScraperStatus } from "@/services/api";


export function useScraperStatus(intervalMs = 1500) {
  const [status, setStatus] = useState("idle");
  const [details, setDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchStatus = async () => {
      try {
        const data = await getScraperStatus();
        if (!cancelled) {
          setStatus(data.status);
          setDetails(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchStatus();
    const intervalId = setInterval(fetchStatus, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [intervalMs]);

  return { status, details, isLoading, error };
}
