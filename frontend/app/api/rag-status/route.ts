import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

interface PipelineState {
  pipeline_id: string;
  pipeline_type: string;
  server_status: string;
  last_heartbeat: string | null;
  status_details: Record<string, unknown> | null;
  last_check_time: string | null;
  known_files: Record<string, unknown> | null;
  last_run: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface FileInfo {
  name: string;
  id?: string;
  started_at: string;
  completed_at?: string;
}

interface ResponseData {
  status: string;
  pipelines: Array<{
    pipeline_id: string;
    pipeline_type: string;
    server_status: string;
    last_heartbeat: string | null;
    status_details: Record<string, unknown>;
    is_active: boolean;
  }>;
  serverTime: string;
  status_details?: Record<string, unknown>;
  last_activity?: string;
  files_processing?: FileInfo[];
  files_completed?: FileInfo[];
  files_failed?: FileInfo[];
}

// Simple in-memory cache to reduce database hits
interface CachedResponse {
  data: ResponseData;
  timestamp: number;
}

let cache: CachedResponse | null = null;
const CACHE_TTL = 8000; // 8 seconds cache - longer than most polling intervals

export async function GET(request: NextRequest) {
  try {
    // Check cache first
    const currentTime = Date.now();
    if (cache && (currentTime - cache.timestamp < CACHE_TTL)) {
      return NextResponse.json(cache.data);
    }

    // Get pipeline_id from query params (optional)
    const url = new URL(request.url);
    const pipelineId = url.searchParams.get("pipeline_id");
    
    // Create Supabase client with service role key
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    
    if (!supabaseUrl || !supabaseServiceKey) {
      console.error("[RAG-STATUS-API] Missing Supabase configuration");
      return NextResponse.json(
        {
          error: "Configuration error", 
          status: "error",
          message: "Supabase configuration missing",
        },
        { status: 500 }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);
    
    // Query the rag_pipeline_state table
    let query = supabase
      .from("rag_pipeline_state")
      .select("*");
    
    if (pipelineId) {
      query = query.eq("pipeline_id", pipelineId);
    }
    
    const { data, error } = await query;
    
    if (error) {
      console.error("[RAG-STATUS-API] Supabase query error:", error);
      return NextResponse.json(
        {
          error: "Database error",
          status: "error",
          message: error.message,
        },
        { status: 500 }
      );
    }
    
    // If no data, return offline status
    if (!data || data.length === 0) {
      return NextResponse.json({
        status: "offline",
        pipelines: [],
        message: "No RAG pipelines found",
        serverTime: new Date().toISOString(),
      });
    }
    
    // Type the data
    const pipelines = data as PipelineState[];
    
    // Check for any online pipelines
    const onlinePipelines = pipelines.filter((p: PipelineState) => p.server_status === "online");
    
    // Check for stale heartbeats (more than 2 minutes old)
    const now = new Date();
    const activeOnlinePipelines = onlinePipelines.filter((p: PipelineState) => {
      if (!p.last_heartbeat) return false;
      const lastHeartbeat = new Date(p.last_heartbeat);
      const timeDiff = now.getTime() - lastHeartbeat.getTime();
      return timeDiff < 120000; // 2 minutes
    });
    
    // Debug logging
    console.log("[RAG-STATUS-API] Debug:", {
      totalPipelines: pipelines.length,
      onlinePipelines: onlinePipelines.length,
      activeOnlinePipelines: activeOnlinePipelines.length,
      pipelineStatuses: pipelines.map(p => ({ id: p.pipeline_id, status: p.server_status, heartbeat: p.last_heartbeat }))
    });
    
    // Prepare response
    const response: ResponseData = {
      status: activeOnlinePipelines.length > 0 ? "online" : "offline",
      pipelines: pipelines.map((p: PipelineState) => ({
        pipeline_id: p.pipeline_id,
        pipeline_type: p.pipeline_type,
        server_status: p.server_status,
        last_heartbeat: p.last_heartbeat,
        status_details: p.status_details || {},
        is_active: activeOnlinePipelines.some((ap: PipelineState) => ap.pipeline_id === p.pipeline_id),
      })),
      serverTime: new Date().toISOString(),
    };
    
    // If there are any active pipelines, include their status details
    if (activeOnlinePipelines.length > 0) {
      const primaryPipeline = activeOnlinePipelines[0];
      response.status_details = primaryPipeline.status_details || {};
      response.last_activity = primaryPipeline.status_details?.last_activity as string;
      response.files_processing = (primaryPipeline.status_details?.files_processing as FileInfo[]) || [];
      response.files_completed = (primaryPipeline.status_details?.files_completed as FileInfo[]) || [];
      response.files_failed = (primaryPipeline.status_details?.files_failed as FileInfo[]) || [];
    }
    
    // Cache the response
    cache = {
      data: response,
      timestamp: Date.now()
    };
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error("[RAG-STATUS-API] Unexpected error:", error);
    return NextResponse.json(
      {
        error: "Internal server error",
        status: "error",
        message: "Failed to fetch RAG pipeline status",
      },
      { status: 500 }
    );
  }
}

// Handle CORS preflight
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}