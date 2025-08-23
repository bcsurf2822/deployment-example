"use client";

import React, { useState, useEffect } from "react";

interface PipelineStatus {
  status: string;
  pipeline_type: string | null;
  last_check_time: string | null;
  next_check_time: string | null;
  files_processing: Array<{
    name: string;
    id?: string;
    started_at: string;
  }>;
  files_completed: Array<{
    name: string;
    id?: string;
    started_at: string;
    completed_at: string;
  }>;
  files_failed: Array<{
    name: string;
    id?: string;
    started_at: string;
    completed_at: string;
  }>;
  total_processed: number;
  total_failed: number;
  check_interval: number;
  is_checking: boolean;
  seconds_until_next_check?: number;
  last_activity: string;
}

// Check if polling should be disabled (for development/debugging)
const DISABLE_RAG_POLLING = process.env.NEXT_PUBLIC_DISABLE_RAG_POLLING === 'true';
const MIN_POLL_INTERVAL = parseInt(process.env.NEXT_PUBLIC_RAG_POLL_INTERVAL || '10000');

export default function RAGPipelineStatus() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(false);
  const [countdown, setCountdown] = useState<number>(0);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);

  useEffect(() => {
    // Skip if polling is disabled
    if (DISABLE_RAG_POLLING) {
      setError("RAG status polling is disabled");
      return;
    }

    // Fetch status with smart polling intervals
    const fetchStatus = async () => {
      try {
        setLastFetch(new Date());
        
        // Fetch from our API route which now reads from Supabase
        const response = await fetch("/api/rag-status");
        
        if (response.ok) {
          const data = await response.json();
          
          // Check if we got an error response from the API
          if (data.error || data.status === "offline") {
            setIsOnline(false);
            setError(data.message || "Pipeline offline or unreachable");
            setStatus(null);
          } else {
            setStatus(data);
            setIsOnline(true);
            setError(null);
            
            // Set initial countdown
            if (data.seconds_until_next_check) {
              setCountdown(data.seconds_until_next_check);
            }
          }
        } else {
          throw new Error(`API returned status ${response.status}`);
        }
      } catch (err) {
        console.error("[RAG-STATUS] Error fetching pipeline status:", err);
        setIsOnline(false);
        setError("Unable to fetch pipeline status");
        setStatus(null);
      }
    };

    // Initial fetch
    fetchStatus();

    // Set up smart polling intervals:
    // - Default: MIN_POLL_INTERVAL (10 seconds by default)
    // - Every 30 seconds when pipeline is offline
    // - Every 5 seconds when files are processing (more responsive)
    let pollInterval = MIN_POLL_INTERVAL;
    
    if (!isOnline) {
      pollInterval = Math.max(30000, MIN_POLL_INTERVAL); // At least 30 seconds when offline
    } else if (status?.files_processing && status.files_processing.length > 0) {
      pollInterval = Math.min(5000, MIN_POLL_INTERVAL); // 5 seconds when processing files (unless MIN is higher)
    }

    const interval = setInterval(fetchStatus, pollInterval);

    return () => clearInterval(interval);
  }, []); // Empty dependency array - only run once on mount

  // Countdown timer
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const formatTime = (isoString: string): string => {
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(new Date(isoString));
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return minutes > 0 ? `${minutes}m ${secs}s` : `${secs}s`;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {/* Header with status indicator */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-semibold text-gray-900">
            RAG Pipeline Status
          </h3>
          <div className="flex items-center space-x-2">
            <div
              className={`h-3 w-3 rounded-full ${
                isOnline ? "bg-green-500 animate-pulse" : "bg-red-500"
              }`}
            />
            <span className="text-sm text-gray-600">
              {isOnline ? "Online" : "Offline"}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          {status && (
            <div className="text-sm text-gray-500">
              Type: {status.pipeline_type || "Unknown"}
            </div>
          )}
          {lastFetch && (
            <div className="text-xs text-gray-400">
              Updated: {formatTime(lastFetch.toISOString())}
            </div>
          )}
        </div>
      </div>

      {error && !isOnline && (
        <div className="text-center py-8 text-gray-500">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-sm">{error}</p>
          <p className="text-xs text-gray-400 mt-2">
            Make sure the RAG pipeline is running
          </p>
        </div>
      )}

      {status && isOnline && (
        <div className="space-y-4">
          {/* Next check countdown */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Next check in:</span>
              <span className="text-lg font-mono font-semibold text-blue-600">
                {status.is_checking ? "Checking now..." : formatDuration(countdown)}
              </span>
            </div>
            {status.last_check_time && (
              <div className="mt-1 text-xs text-gray-500">
                Last check: {formatTime(status.last_check_time)}
              </div>
            )}
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-600">
                {status.total_processed}
              </div>
              <div className="text-xs text-green-700">Files Processed</div>
            </div>
            <div className="bg-red-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-red-600">
                {status.total_failed}
              </div>
              <div className="text-xs text-red-700">Failed</div>
            </div>
          </div>

          {/* Currently Processing */}
          {status.files_processing.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Currently Processing ({status.files_processing.length})
              </h4>
              <ul className="space-y-1">
                {status.files_processing.map((file, index) => (
                  <li
                    key={index}
                    className="flex items-center space-x-2 text-sm"
                  >
                    <svg
                      className="animate-spin h-4 w-4 text-blue-500"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <span className="text-gray-700 truncate">{file.name}</span>
                    <span className="text-xs text-gray-500">
                      {formatTime(file.started_at)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recently Completed */}
          {status.files_completed.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Recently Completed
              </h4>
              <ul className="space-y-1">
                {status.files_completed.slice(0, 3).map((file, index) => (
                  <li
                    key={index}
                    className="flex items-center space-x-2 text-sm"
                  >
                    <svg
                      className="h-4 w-4 text-green-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-700 truncate">{file.name}</span>
                    <span className="text-xs text-gray-500">
                      {formatTime(file.completed_at)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* No documents message */}
          {status.files_processing.length === 0 &&
            status.files_completed.length === 0 &&
            status.total_processed === 0 && (
              <div className="text-center py-4 text-gray-500">
                <p className="text-sm">No documents currently</p>
                <p className="text-xs text-gray-400 mt-1">
                  Upload files to Google Drive to start processing
                </p>
              </div>
            )}
        </div>
      )}
    </div>
  );
}