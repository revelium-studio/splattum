declare module "@mkkellogg/gaussian-splats-3d" {
  export enum LogLevel {
    None = 0,
    Error = 1,
    Warning = 2,
    Info = 3,
    Debug = 4,
  }

  export enum SceneFormat {
    Ply = 0,
    Splat = 1,
    Ksplat = 2,
  }

  export interface ViewerOptions {
    cameraUp?: [number, number, number];
    initialCameraPosition?: [number, number, number];
    initialCameraLookAt?: [number, number, number];
    rootElement?: HTMLElement;
    selfDrivenMode?: boolean;
    useBuiltInControls?: boolean;
    dynamicScene?: boolean;
    sharedMemoryForWorkers?: boolean;
    antialiased?: boolean;
    logLevel?: LogLevel;
    splatSortDistanceMapPrecision?: number;
    sphericalHarmonicsDegree?: number;
    integerBasedSort?: boolean;
    halfPrecisionCovariancesOnGPU?: boolean;
  }

  export interface SplatSceneOptions {
    splatAlphaRemovalThreshold?: number;
    showLoadingUI?: boolean;
    progressiveLoad?: boolean;
    format?: SceneFormat;
    onProgress?: (progress: number, message?: string) => void;
  }

  export class Viewer {
    constructor(options?: ViewerOptions);
    addSplatScene(url: string, options?: SplatSceneOptions): Promise<void>;
    start(): void;
    stop(): void;
    dispose(): void;
    setCamera?(
      position: [number, number, number],
      lookAt: [number, number, number],
      up: [number, number, number]
    ): void;
  }
}
