/**
 * Outpainting API Client
 * 
 * This module provides utilities for extending splat scenes using AI outpainting.
 * 
 * CONFIGURATION:
 * - Set REPLICATE_API_TOKEN in environment variables
 * - Adjust ARC_DEGREES for 180° → 360° extension
 * - Adjust SAMPLING_DENSITY for more/fewer splats
 */

// ============================================================================
// CONFIGURABLE PARAMETERS
// ============================================================================

/**
 * Arc size in degrees for the extended environment.
 * 180 = half ring around the original
 * 360 = full ring around the original
 */
export const ARC_DEGREES = 180;

/**
 * Sampling density for splat generation.
 * Higher = more splats, more detailed but slower
 * Range: 0.1 (sparse) to 1.0 (dense)
 */
export const SAMPLING_DENSITY = 0.4;

/**
 * Minimum brightness threshold for generating splats (0-255)
 * Pixels darker than this won't generate splats
 */
export const MIN_BRIGHTNESS_THRESHOLD = 15;

// ============================================================================
// TYPES
// ============================================================================

export interface OutpaintOptions {
  prompt?: string;
  negativePrompt?: string;
  width?: number;
  height?: number;
  steps?: number;
  guidanceScale?: number;
}

export interface SplatData {
  /** 3D position [x, y, z] */
  position: [number, number, number];
  /** RGB color [r, g, b] normalized 0-1 */
  color: [number, number, number];
  /** Splat size/scale */
  size: number;
  /** Opacity 0-1 */
  opacity: number;
}

export interface OutpaintResult {
  imageBase64: string;
  splats: SplatData[];
}

// ============================================================================
// CANVAS UTILITIES
// ============================================================================

/**
 * Captures the WebGL canvas as a base64 PNG
 * Note: WebGL canvases may have issues with preserveDrawingBuffer
 * We try multiple approaches to ensure capture works
 */
export function captureCanvasAsBase64(canvas: HTMLCanvasElement): string {
  // Try direct toDataURL first (works if preserveDrawingBuffer is true)
  try {
    const dataUrl = canvas.toDataURL("image/png");
    const base64 = dataUrl.split(",")[1];
    
    // Check if we got a valid image (not blank)
    if (base64 && base64.length > 1000) {
      console.log("Direct canvas capture successful, size:", base64.length);
      return base64;
    }
  } catch (e) {
    console.warn("Direct canvas capture failed:", e);
  }
  
  // Fallback: copy to 2D canvas
  const tempCanvas = document.createElement("canvas");
  tempCanvas.width = canvas.width;
  tempCanvas.height = canvas.height;
  const ctx = tempCanvas.getContext("2d");
  
  if (!ctx) {
    throw new Error("Failed to get 2D context");
  }
  
  ctx.drawImage(canvas, 0, 0);
  
  const dataUrl = tempCanvas.toDataURL("image/png");
  console.log("Fallback canvas capture, size:", dataUrl.length);
  return dataUrl.split(",")[1];
}

/**
 * Captures canvas at a specific resolution with the original centered
 * For outpainting, we create a larger canvas and put the original in the center
 */
export function captureCanvasAtResolution(
  canvas: HTMLCanvasElement,
  targetWidth: number,
  targetHeight: number
): string {
  console.log("Capturing canvas:", canvas.width, "x", canvas.height, "->", targetWidth, "x", targetHeight);
  
  const tempCanvas = document.createElement("canvas");
  tempCanvas.width = targetWidth;
  tempCanvas.height = targetHeight;
  const ctx = tempCanvas.getContext("2d");
  
  if (!ctx) {
    throw new Error("Failed to get 2D context");
  }
  
  // Fill with black first (areas to be outpainted)
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, targetWidth, targetHeight);
  
  // Calculate centered position - place original in center at ~60% of the canvas
  const innerSize = Math.min(targetWidth, targetHeight) * 0.6;
  const scale = Math.min(innerSize / canvas.width, innerSize / canvas.height);
  const scaledWidth = canvas.width * scale;
  const scaledHeight = canvas.height * scale;
  const offsetX = (targetWidth - scaledWidth) / 2;
  const offsetY = (targetHeight - scaledHeight) / 2;
  
  console.log("Drawing original at:", offsetX, offsetY, scaledWidth, scaledHeight);
  
  // For WebGL, try to get a fresh image first
  try {
    // Create an intermediate canvas to ensure we capture the WebGL content
    const glCanvas = document.createElement("canvas");
    glCanvas.width = canvas.width;
    glCanvas.height = canvas.height;
    const glCtx = glCanvas.getContext("2d");
    if (glCtx) {
      glCtx.drawImage(canvas, 0, 0);
      ctx.drawImage(glCanvas, offsetX, offsetY, scaledWidth, scaledHeight);
    } else {
      ctx.drawImage(canvas, offsetX, offsetY, scaledWidth, scaledHeight);
    }
  } catch (e) {
    // Fallback to direct draw
    ctx.drawImage(canvas, offsetX, offsetY, scaledWidth, scaledHeight);
  }
  
  const dataUrl = tempCanvas.toDataURL("image/png");
  return dataUrl.split(",")[1];
}

/**
 * Returns the bounds of the original image within the target canvas
 */
export function getOriginalBounds(
  canvasWidth: number,
  canvasHeight: number,
  targetWidth: number,
  targetHeight: number
): { x: number; y: number; width: number; height: number } {
  const innerSize = Math.min(targetWidth, targetHeight) * 0.6;
  const scale = Math.min(innerSize / canvasWidth, innerSize / canvasHeight);
  const scaledWidth = canvasWidth * scale;
  const scaledHeight = canvasHeight * scale;
  const offsetX = (targetWidth - scaledWidth) / 2;
  const offsetY = (targetHeight - scaledHeight) / 2;
  
  return { x: offsetX, y: offsetY, width: scaledWidth, height: scaledHeight };
}

/**
 * Creates a mask for outpainting (white = areas to generate, black = keep original)
 * Must match the exact positioning used in captureCanvasAtResolution
 */
export function createOutpaintMask(
  originalWidth: number,
  originalHeight: number,
  targetWidth: number,
  targetHeight: number
): string {
  const canvas = document.createElement("canvas");
  canvas.width = targetWidth;
  canvas.height = targetHeight;
  const ctx = canvas.getContext("2d");
  
  if (!ctx) {
    throw new Error("Failed to get 2D context");
  }
  
  // Fill everything white (areas to generate)
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, targetWidth, targetHeight);
  
  // Calculate where the original image is centered
  const bounds = getOriginalBounds(originalWidth, originalHeight, targetWidth, targetHeight);
  
  // Fill the original area black (keep) - with slight feathering
  const padding = 8;
  ctx.fillStyle = "#000000";
  ctx.fillRect(
    bounds.x + padding, 
    bounds.y + padding, 
    bounds.width - padding * 2, 
    bounds.height - padding * 2
  );
  
  const dataUrl = canvas.toDataURL("image/png");
  return dataUrl.split(",")[1];
}

// ============================================================================
// SPLAT GENERATION
// ============================================================================

/**
 * Generates splats from the outpainted border regions
 * Creates a 180° arc of splats around the original scene
 * 
 * The splats are positioned in 3D space to wrap around the scene:
 * - Left border pixels → left side of the arc
 * - Right border pixels → right side of the arc
 * - Top border pixels → upper arc area
 * - Bottom border pixels → lower arc area
 * 
 * Colors are sampled directly from the AI-generated pixels.
 */
export function generateExtendedSplatsFromOutpaint(
  originalCanvas: HTMLCanvasElement,
  outpaintedImage: HTMLImageElement,
  arcDegrees: number = ARC_DEGREES,
  density: number = SAMPLING_DENSITY
): SplatData[] {
  const splats: SplatData[] = [];
  
  // Create canvas for pixel analysis
  const outpaintCanvas = document.createElement("canvas");
  outpaintCanvas.width = outpaintedImage.width;
  outpaintCanvas.height = outpaintedImage.height;
  const outpaintCtx = outpaintCanvas.getContext("2d", { willReadFrequently: true });
  
  if (!outpaintCtx) {
    throw new Error("Failed to get 2D context");
  }
  
  outpaintCtx.drawImage(outpaintedImage, 0, 0);
  
  // Calculate the original image bounds within the outpainted image
  const bounds = getOriginalBounds(
    originalCanvas.width,
    originalCanvas.height,
    outpaintedImage.width,
    outpaintedImage.height
  );
  
  // Get pixel data
  const imageData = outpaintCtx.getImageData(
    0, 0, 
    outpaintedImage.width, 
    outpaintedImage.height
  );
  const pixels = imageData.data;
  
  // 3D scene parameters
  const sceneRadius = 4;      // How far from center the arc is placed
  const depthVariation = 2;   // How much the splats vary in depth
  const verticalSpread = 3;   // Vertical spread of splats
  
  // Image center
  const imgCenterX = outpaintedImage.width / 2;
  const imgCenterY = outpaintedImage.height / 2;
  
  // Sampling step based on density
  const step = Math.max(1, Math.floor(4 / density));
  
  // Sample pixels in the border regions
  for (let y = 0; y < outpaintedImage.height; y += step) {
    for (let x = 0; x < outpaintedImage.width; x += step) {
      // Check if this pixel is in the border region (outside original)
      const isInOriginal = (
        x >= bounds.x &&
        x < bounds.x + bounds.width &&
        y >= bounds.y &&
        y < bounds.y + bounds.height
      );
      
      if (isInOriginal) continue;
      
      const pixelIndex = (y * outpaintedImage.width + x) * 4;
      const r = pixels[pixelIndex];
      const g = pixels[pixelIndex + 1];
      const b = pixels[pixelIndex + 2];
      const a = pixels[pixelIndex + 3];
      
      // Calculate brightness
      const brightness = (r + g + b) / 3;
      
      // Skip very dark or transparent pixels
      if (brightness < MIN_BRIGHTNESS_THRESHOLD || a < 128) continue;
      
      // Add randomness to avoid grid patterns
      if (Math.random() > density * 1.2) continue;
      
      // Normalize pixel position relative to image center (-1 to 1)
      const normalizedX = (x - imgCenterX) / imgCenterX;
      const normalizedY = (y - imgCenterY) / imgCenterY;
      
      // Calculate angle based on position around the image
      // The arc spans from -arcDegrees/2 to +arcDegrees/2
      const halfArc = (arcDegrees / 2) * (Math.PI / 180);
      
      // Map the X position to an angle in the arc
      // Pixels on the left (normalizedX = -1) map to -halfArc
      // Pixels on the right (normalizedX = 1) map to +halfArc
      const angle = normalizedX * halfArc;
      
      // Distance from center affects how far back in the scene the splat is placed
      const distFromCenter = Math.sqrt(normalizedX * normalizedX + normalizedY * normalizedY);
      
      // Calculate 3D position
      // X: Arc position (left/right)
      // Y: Vertical position
      // Z: Depth (front/back based on arc and distance)
      const radius = sceneRadius + distFromCenter * depthVariation * 0.5;
      
      const splatX = Math.sin(angle) * radius + (Math.random() - 0.5) * 0.3;
      const splatY = normalizedY * verticalSpread + (Math.random() - 0.5) * 0.2;
      const splatZ = 5 + Math.cos(angle) * radius * 0.3 + distFromCenter * depthVariation;
      
      // Size based on brightness and distance (further = slightly larger to compensate)
      const baseSize = 0.015 + (brightness / 255) * 0.04;
      const distanceScale = 1 + distFromCenter * 0.3;
      const size = baseSize * distanceScale + Math.random() * 0.01;
      
      // Opacity based on brightness, with falloff at edges
      const edgeFalloff = 1 - distFromCenter * 0.3;
      const opacity = Math.max(0.2, Math.min(0.85, (brightness / 255) * 0.6 * edgeFalloff + 0.25));
      
      splats.push({
        position: [splatX, splatY, splatZ],
        color: [r / 255, g / 255, b / 255],
        size,
        opacity,
      });
    }
  }
  
  console.log(`Generated ${splats.length} extended splats from outpainted regions`);
  return splats;
}

/**
 * Loads a base64 PNG as an HTMLImageElement
 */
export function loadBase64Image(base64: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = `data:image/png;base64,${base64}`;
  });
}
