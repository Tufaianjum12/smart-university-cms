// Wraps fetchHealth() with loading/error/data state so the page component
// stays declarative (it just reads { status, error, data } instead of
// managing useState/useEffect plumbing itself). This is the pattern every
// future data-fetching hook (useAttendance, useGpa, ...) will follow.

import { useEffect, useState } from "react";
import { fetchHealth } from "../services/healthService";

export function useHealthCheck() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("loading"); // "loading" | "success" | "error"

  useEffect(() => {
    let isMounted = true;

    fetchHealth()
      .then((result) => {
        if (!isMounted) return;
        setData(result);
        setStatus("success");
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err);
        setStatus("error");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return { data, error, status };
}
