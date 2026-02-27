import { NextRequest, NextResponse } from "next/server";
import { writeFile, mkdir, readdir, readFile } from "fs/promises";
import { spawn } from "child_process";
import path from "path";
import { existsSync } from "fs";

// CORS headers to allow cross-origin requests from router domain
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "https://lab.revelium.studio",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, X-Requested-With",
  "Access-Control-Allow-Credentials": "true",
  "Access-Control-Max-Age": "86400",
};

// Helper to add CORS headers to response
function corsResponse(response: NextResponse): NextResponse {
  Object.entries(CORS_HEADERS).forEach(([key, value]) => {
    response.headers.set(key, value);
  });
  return response;
}

// Check if running on Vercel
const IS_VERCEL = process.env.VERCEL === "1";

// Modal configuration for GPU processing (replacing RunPod)
// Deploy modal_app.py and get the endpoint URLs
const MODAL_ENDPOINT = process.env.MODAL_ENDPOINT || "https://revelium-studio--diffsplat-process-image-endpoint.modal.run";
const MODAL_STATUS_ENDPOINT = process.env.MODAL_STATUS_ENDPOINT || "https://revelium-studio--diffsplat-get-job-status-endpoint.modal.run";

// Paths for local development
const PROJECT_ROOT = path.resolve(process.cwd(), "..");
const UPLOADS_DIR = path.join(process.cwd(), "public", "uploads");
const OUTPUTS_DIR = path.join(process.cwd(), "public", "outputs");
const JOBS_DIR = path.join(process.cwd(), ".jobs");

// Allow long-running requests (5 minutes for Enterprise, but check Vercel plan limits)
export const maxDuration = 300;

interface JobStatus {
  status: "processing" | "completed" | "failed";
  splatUrl?: string;
  plyBase64?: string;
  error?: string;
  fileName: string;
  startTime: number;
  callId?: string; // Modal call_id for async jobs
}

async function saveJobStatus(jobId: string, status: JobStatus) {
  await mkdir(JOBS_DIR, { recursive: true });
  await writeFile(path.join(JOBS_DIR, `${jobId}.json`), JSON.stringify(status));
}

async function getJobStatus(jobId: string): Promise<JobStatus | null> {
  const filePath = path.join(JOBS_DIR, `${jobId}.json`);
  if (!existsSync(filePath)) return null;
  const data = await readFile(filePath, "utf-8");
  return JSON.parse(data);
}

// Process with Modal (GPU cloud)
async function processWithModal(
  imageBase64: string,
  filename: string,
  prompt: string = "",
  elevation: number = 20
): Promise<{ callId: string } | { plyBase64: string }> {
  console.log(`🚀 Sending image to Modal DiffSplat endpoint...`);
  console.log(`📍 Modal endpoint: ${MODAL_ENDPOINT}`);

  const response = await fetch(MODAL_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image: imageBase64,
      filename: filename,
      prompt: prompt,
      elevation: elevation,
      async: true, // Use async mode to avoid timeout
    }),
    signal: AbortSignal.timeout(60000), // 60 second timeout for job creation
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`❌ Modal request failed: ${response.status} - ${errorText}`);
    throw new Error(`Failed to process with Modal: ${response.status} - ${errorText}`);
  }

  const result = await response.json();
  
  if (result.error) {
    throw new Error(result.error);
  }
  
  // Check if async job was created
  if (result.call_id) {
    console.log(`✅ Modal async job created with call_id: ${result.call_id}`);
    return { callId: result.call_id };
  }
  
  // Synchronous result
  if (result.ply) {
    console.log(`✅ Modal returned synchronous result`);
    return { plyBase64: result.ply };
  }
  
  throw new Error("Unexpected response from Modal");
}

// Process locally with DiffSplat - for local dev (if set up)
function processLocally(
  inputPath: string,
  outputDir: string,
  jobId: string,
  fileName: string
) {
  const venvActivate = path.join(PROJECT_ROOT, ".venv", "bin", "activate");

  // Note: Local DiffSplat processing requires the full setup
  // This is a placeholder - for local dev, you might want to use Modal directly
  const child = spawn(
    "bash",
    [
      "-c",
      `source "${venvActivate}" && python -c "print('Local DiffSplat not configured. Use Modal deployment.')"`,
    ],
    {
      cwd: PROJECT_ROOT,
      env: {
        ...process.env,
        PATH: `${PROJECT_ROOT}/.venv/bin:${process.env.PATH}`,
      },
    }
  );

  child.stdout.on("data", (data) => {
    console.log("DiffSplat:", data.toString());
  });

  child.stderr.on("data", (data) => {
    console.log("DiffSplat stderr:", data.toString());
  });

  child.on("close", async () => {
    try {
      const outputFiles = await readdir(outputDir);
      const plyFile = outputFiles.find((f) => f.endsWith(".ply"));

      if (plyFile) {
        const splatUrl = `/outputs/${jobId}/${plyFile}`;
        console.log("Job completed successfully:", jobId, splatUrl);
        await saveJobStatus(jobId, {
          status: "completed",
          splatUrl,
          fileName,
          startTime: Date.now(),
        });
      } else {
        await saveJobStatus(jobId, {
          status: "failed",
          error: "No output file generated. Local DiffSplat processing not configured.",
          fileName,
          startTime: Date.now(),
        });
      }
    } catch (error) {
      await saveJobStatus(jobId, {
        status: "failed",
        error: error instanceof Error ? error.message : "Unknown error",
        fileName,
        startTime: Date.now(),
      });
    }
  });

  child.on("error", async (error) => {
    await saveJobStatus(jobId, {
      status: "failed",
      error: error.message,
      fileName,
      startTime: Date.now(),
    });
  });
}

// Handle CORS preflight requests
export async function OPTIONS(request: NextRequest) {
  const response = new NextResponse(null, { status: 204 });
  return corsResponse(response);
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("image") as File;
    const prompt = (formData.get("prompt") as string) || "";
    const elevation = parseInt((formData.get("elevation") as string) || "20", 10);

    if (!file) {
      return corsResponse(NextResponse.json({ error: "No image provided" }, { status: 400 }));
    }

    const jobId = Date.now().toString();
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    if (IS_VERCEL) {
      // Use Modal for GPU processing
      console.log("🚀 Starting Modal DiffSplat processing (Vercel)...");

      const imageBase64 = buffer.toString("base64");

      try {
        const result = await processWithModal(imageBase64, file.name, prompt, elevation);
        
        if ("callId" in result) {
          // Async job - return job ID for polling
          console.log(`✅ Modal async job created with call_id: ${result.callId}`);
          return corsResponse(NextResponse.json({
            success: true,
            jobId: result.callId,
            message: "Processing started asynchronously on Modal",
          }));
        } else {
          // Synchronous result
          console.log(`✅ Modal returned synchronous result`);
          return corsResponse(NextResponse.json({
            success: true,
            status: "completed",
            plyBase64: result.plyBase64,
          }));
        }
      } catch (modalError) {
        const errorMessage = modalError instanceof Error ? modalError.message : "Failed to process with Modal";
        console.error("❌ Failed to process with Modal:", errorMessage);
        
        return corsResponse(NextResponse.json(
          {
            error: "Failed to start processing job. Please try again in a few minutes."
          },
          { status: 503 }
        ));
      }
    } else {
      // Local development - try to use Modal API directly
      console.log("🚀 Using Modal API for local development...");
      
      const imageBase64 = buffer.toString("base64");
      
      try {
        const result = await processWithModal(imageBase64, file.name, prompt, elevation);
        
        if ("callId" in result) {
          return corsResponse(NextResponse.json({
            success: true,
            jobId: result.callId,
            message: "Processing started on Modal",
          }));
        } else {
          return corsResponse(NextResponse.json({
            success: true,
            status: "completed",
            plyBase64: result.plyBase64,
          }));
        }
      } catch (error) {
        console.error("❌ Modal API failed, falling back to local processing...", error);
        
        // Fallback to local processing
        await mkdir(UPLOADS_DIR, { recursive: true });
        await mkdir(OUTPUTS_DIR, { recursive: true });

        const sanitizedName = file.name.replace(/[^a-zA-Z0-9.-]/g, "_");
        const inputFileName = `${jobId}_${sanitizedName}`;
        const inputPath = path.join(UPLOADS_DIR, inputFileName);

        await writeFile(inputPath, buffer);

        const outputDir = path.join(OUTPUTS_DIR, jobId);
        await mkdir(outputDir, { recursive: true });

        await saveJobStatus(jobId, {
          status: "processing",
          fileName: file.name,
          startTime: Date.now(),
        });

        console.log("Starting local DiffSplat job:", jobId);
        processLocally(inputPath, outputDir, jobId, file.name);

        return corsResponse(NextResponse.json({
          success: true,
          jobId,
          message: "Processing started locally",
        }));
      }
    }
  } catch (error) {
    console.error("Error processing:", error);
    const errorResponse = NextResponse.json(
      {
        error:
          error instanceof Error ? error.message : "Failed to process image",
      },
      { status: 500 }
    );
    return corsResponse(errorResponse);
  }
}

// GET for polling job status (Modal async jobs)
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const jobId = searchParams.get("jobId");

  if (!jobId) {
    return corsResponse(NextResponse.json({ error: "No jobId provided" }, { status: 400 }));
  }

  // Check if this looks like a Modal call_id (starts with "fc-")
  const isModalJob = jobId.startsWith("fc-");
  
  if (IS_VERCEL || isModalJob) {
    // Poll Modal for job status
    try {
      console.log(`🔍 Polling Modal status for call_id: ${jobId}`);
      
      const statusUrl = `${MODAL_STATUS_ENDPOINT}?call_id=${encodeURIComponent(jobId)}`;
      console.log(`🌐 Checking status at: ${statusUrl}`);
      
      const response = await fetch(statusUrl, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        signal: AbortSignal.timeout(30000), // 30 second timeout
      });
      
      console.log(`📍 Modal status response: ${response.status}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ Modal status check failed: ${response.status} - ${errorText}`);
        
        // Return processing status as fallback
        return corsResponse(NextResponse.json({ 
          status: "processing",
          fileName: "",
          startTime: Date.now(),
        }));
      }

      const modalStatus = await response.json();
      console.log(`📊 Modal status response:`, JSON.stringify(modalStatus, null, 2));

      if (modalStatus.status === "completed") {
        console.log(`✅ Modal job completed`);
        return corsResponse(NextResponse.json({
          status: "completed",
          plyBase64: modalStatus.ply,
          fileName: "",
          startTime: Date.now(),
        }));
      } else if (modalStatus.status === "failed") {
        console.error(`❌ Modal job failed:`, modalStatus.error);
        return corsResponse(NextResponse.json({
          status: "failed",
          error: modalStatus.error || "Processing failed",
          fileName: "",
          startTime: Date.now(),
        }));
      } else {
        // Still processing
        console.log(`⏳ Modal job still processing`);
        return corsResponse(NextResponse.json({
          status: "processing",
          modalStatus: modalStatus.status,
          fileName: "",
          startTime: Date.now(),
        }));
      }
    } catch (error) {
      console.error("❌ Error polling Modal status:", error);
      // If Modal API fails, assume still processing
      return corsResponse(NextResponse.json({
        status: "processing",
        fileName: "",
        startTime: Date.now(),
      }));
    }
  } else {
    // Local processing - use file-based status
    const status = await getJobStatus(jobId);

    if (!status) {
      return corsResponse(NextResponse.json({ 
        status: "processing", 
        fileName: "",
        startTime: Date.now(),
      }));
    }

    return corsResponse(NextResponse.json(status));
  }
}
