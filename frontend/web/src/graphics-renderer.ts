import { ACESFilmicToneMapping, PCFShadowMap, WebGPURenderer } from "three/webgpu";

/** Native WebGPU when available; Three.js performs adapter-failure WebGL2 fallback. */
export async function createGraphicsRenderer(forceWebGL: boolean, onFailure: () => void) {
  const renderer = new WebGPURenderer({ antialias: true, alpha: false, forceWebGL });
  let failure: Error | null = null;
  const markFailed = () => {
    if (failure) return;
    failure = new Error("Graphics backend failed");
    onFailure();
    // Initialization may still be pending; stopping is best-effort on a failed backend.
    void renderer.setAnimationLoop(null).catch(() => {});
  };
  const assertHealthy = () => { if (failure) throw failure; };
  const originalDeviceLost = renderer.onDeviceLost.bind(renderer);
  const originalError = renderer.onError.bind(renderer);
  renderer.onDeviceLost = (info) => {
    // Three's handler also sets its internal lost-device guard; do not replace it.
    originalDeviceLost(info);
    markFailed();
  };
  renderer.onError = (error) => { originalError(error); markFailed(); };
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = PCFShadowMap;
  try {
    await renderer.init();
    assertHealthy();
    return { renderer, assertHealthy };
  } catch (error) {
    await renderer.dispose();
    throw error;
  }
}

export function graphicsBackend(renderer: WebGPURenderer): "WebGPU" | "WebGL2" {
  return "isWebGPUBackend" in renderer.backend ? "WebGPU" : "WebGL2";
}
