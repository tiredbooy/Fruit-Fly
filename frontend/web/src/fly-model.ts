import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { prepareFlyAsset } from "./animated-fly";

export const FLY_ASSET_URL = new URL("./assets/fly/walking-fly.glb", import.meta.url).href;

/** User-authorized appearance asset only; none of the reference engine is imported. */
export async function loadFlyModel() {
  return prepareFlyAsset(await new GLTFLoader().loadAsync(FLY_ASSET_URL));
}
