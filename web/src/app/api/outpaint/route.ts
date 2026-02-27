/**
 * Outpainting API Route
 * 
 * This route handles AI outpainting requests using Replicate's API.
 * 
 * Environment Variables:
 * - REPLICATE_API_TOKEN: Your Replicate API token
 */

import { NextRequest, NextResponse } from "next/server";

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

// Allow longer execution for AI processing
export const maxDuration = 300;

interface OutpaintRequest {
  /** Base64 encoded PNG of the original image */
  image: string;
  /** Base64 encoded PNG mask (white = generate, black = keep) */
  mask: string;
  /** Prompt for image generation */
  prompt: string;
  /** Negative prompt */
  negativePrompt: string;
  /** Output width */
  width: number;
  /** Output height */
  height: number;
}

/**
 * Outpaint using Replicate's Stable Diffusion Inpainting model
 */
async function outpaintWithReplicate(
  imageBase64: string,
  maskBase64: string,
  prompt: string,
  negativePrompt: string
): Promise<string> {
  const REPLICATE_API_TOKEN = process.env.REPLICATE_API_TOKEN;
  
  if (!REPLICATE_API_TOKEN) {
    throw new Error("REPLICATE_API_TOKEN environment variable is not set");
  }
  
  // Use stability-ai/stable-diffusion-inpainting - the official SD inpainting model
  // Model: https://replicate.com/stability-ai/stable-diffusion-inpainting
  // Version from: https://replicate.com/stability-ai/stable-diffusion-inpainting/versions
  const response = await fetch("https://api.replicate.com/v1/predictions", {
    method: "POST",
    headers: {
      "Authorization": `Token ${REPLICATE_API_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      // Correct version hash from Replicate
      // Stable Diffusion Inpainting - optimized for speed
      version: "95b7223104132402a9ae91cc677285bc5eb997834bd2349fa486f53910fd68b3",
      input: {
        prompt: prompt,
        negative_prompt: negativePrompt,
        image: `data:image/png;base64,${imageBase64}`,
        mask: `data:image/png;base64,${maskBase64}`,
        num_outputs: 1,
        // Reduced from 25 to 20 for faster generation (still high quality)
        num_inference_steps: 20,
        guidance_scale: 7.5,
      },
    }),
  });
  
  if (!response.ok) {
    const errorData = await response.text();
    console.error("Replicate error response:", errorData);
    
    // Parse for details
    try {
      const errorJson = JSON.parse(errorData);
      if (errorJson.detail) {
        throw new Error(`Replicate: ${errorJson.detail}`);
      }
      if (errorJson.title) {
        throw new Error(`Replicate: ${errorJson.title}`);
      }
    } catch (e) {
      if (e instanceof Error && e.message.startsWith("Replicate:")) {
        throw e;
      }
    }
    
    throw new Error(`Replicate API error: ${response.status}`);
  }
  
  let result = await response.json();
  console.log("Initial response status:", result.status);
  console.log("Prediction ID:", result.id);
  
  // Poll for completion
  const maxAttempts = 120;
  let attempts = 0;
  
  while (result.status !== "succeeded" && result.status !== "failed" && result.status !== "canceled" && attempts < maxAttempts) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    
    const pollResponse = await fetch(`https://api.replicate.com/v1/predictions/${result.id}`, {
      headers: {
        "Authorization": `Token ${REPLICATE_API_TOKEN}`,
      },
    });
    
    if (!pollResponse.ok) {
      console.error("Poll error:", await pollResponse.text());
      throw new Error("Failed to poll prediction status");
    }
    
    result = await pollResponse.json();
    attempts++;
    
    if (attempts % 5 === 0) {
      console.log(`Polling attempt ${attempts}, status: ${result.status}`);
    }
  }
  
  if (result.status === "failed") {
    console.error("Prediction failed:", result.error);
    throw new Error(result.error || "Prediction failed");
  }
  
  if (result.status === "canceled") {
    throw new Error("Prediction was canceled");
  }
  
  if (result.status !== "succeeded") {
    throw new Error("Prediction timed out");
  }
  
  // Get the output image URL
  const outputUrl = Array.isArray(result.output) ? result.output[0] : result.output;
  
  if (!outputUrl) {
    console.error("No output in result:", result);
    throw new Error("No output image from Replicate");
  }
  
  console.log("Output URL:", outputUrl);
  
  // Download and convert to base64
  const imageResponse = await fetch(outputUrl);
  if (!imageResponse.ok) {
    throw new Error("Failed to download output image");
  }
  
  const imageBuffer = await imageResponse.arrayBuffer();
  const base64 = Buffer.from(imageBuffer).toString("base64");
  
  return base64;
}

// Handle CORS preflight requests
export async function OPTIONS(request: NextRequest) {
  const response = new NextResponse(null, { status: 204 });
  return corsResponse(response);
}

export async function POST(request: NextRequest) {
  try {
    const body: OutpaintRequest = await request.json();
    
    const { image, mask, prompt, negativePrompt } = body;
    
    if (!image) {
      return corsResponse(NextResponse.json(
        { error: "No image provided" },
        { status: 400 }
      ));
    }
    
    if (!mask) {
      return corsResponse(NextResponse.json(
        { error: "No mask provided" },
        { status: 400 }
      ));
    }
    
    console.log("Outpainting request received");
    console.log("Prompt:", prompt);
    console.log("Image size:", Math.round(image.length / 1024), "KB");
    console.log("Mask size:", Math.round(mask.length / 1024), "KB");
    
    if (!process.env.REPLICATE_API_TOKEN) {
      return corsResponse(NextResponse.json(
        { 
          error: "REPLICATE_API_TOKEN not configured",
          needsConfig: true,
        },
        { status: 503 }
      ));
    }
    
    console.log("Using Replicate API for inpainting");
    
    const resultBase64 = await outpaintWithReplicate(
      image,
      mask,
      prompt,
      negativePrompt
    );
    
    return corsResponse(NextResponse.json({
      success: true,
      image: resultBase64,
    }));
    
  } catch (error) {
    console.error("Outpainting error:", error);
    return corsResponse(NextResponse.json(
      { 
        error: error instanceof Error ? error.message : "Outpainting failed",
      },
      { status: 500 }
    ));
  }
}
