import { expect, test } from "bun:test";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import manifest from "./assets/fly/source-manifest.json";

test("the shipped GLB matches its attribution manifest and stays within the mesh budget", () => {
  const binary = readFileSync(new URL("./assets/fly/drosophila.glb", import.meta.url));
  expect(createHash("sha256").update(binary).digest("hex")).toBe(manifest.glb_sha256);
  expect(binary.readUInt32LE(0)).toBe(0x46546c67);
  expect(binary.readUInt32LE(8)).toBe(binary.length);
  const json = JSON.parse(binary.subarray(20, 20 + binary.readUInt32LE(12)).toString());
  expect(json.meshes).toHaveLength(4);
  expect(json.nodes.map((node: { name: string }) => node.name)).toContain("exoskeleton");
  expect(binary.length).toBeLessThan(2_000_000);
  expect(Object.values(manifest.parts).reduce((sum, part) => sum + part.output_triangles, 0)).toBeLessThanOrEqual(60000);
  expect(manifest.license).toBe("CC-BY-4.0");
});
