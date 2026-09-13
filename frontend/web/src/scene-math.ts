/** Display transforms only; positions and headings always originate in Python. */
export function worldToScene(x: number, y: number, width: number, height: number) {
  return { x: (x / width) * 20, z: -(y / height) * 12 };
}

export function eyeCameraPose(x: number, z: number, heading: number) {
  const forwardX = Math.cos(heading);
  const forwardZ = -Math.sin(heading);
  const eyeX = x + forwardX * 0.8;
  const eyeZ = z + forwardZ * 0.8;
  return {
    position: { x: eyeX, y: 0.65, z: eyeZ },
    target: { x: eyeX + forwardX * 6, y: 0.65, z: eyeZ + forwardZ * 6 },
  };
}

export function interpolateHeading(from: number, to: number, amount: number): number {
  let delta = ((to - from + Math.PI) % (Math.PI * 2)) - Math.PI;
  if (delta < -Math.PI) delta += Math.PI * 2;
  return from + delta * amount;
}

export function odorHaloScale(strength: number | null): number {
  if (strength === null || strength <= 0) return 0;
  return Math.min(2.4, 0.5 + strength);
}

export function neuralIntensity(activity: readonly number[]): number {
  if (!activity.length) return 0;
  return Math.min(1, Math.max(0, activity.reduce((sum, value) => sum + value, 0) / activity.length));
}

export function cameraDistanceFor(radius: number, aspect: number): number {
  const halfFov = Math.min(Math.PI / 8, Math.atan(Math.tan(Math.PI / 8) * aspect));
  return radius / Math.sin(halfFov) * 1.05;
}

/** Fit arena corners to the oblique 45-degree camera, including pedestal depth. */
export function arenaCameraDistance(aspect: number): number {
  const directionLength = Math.hypot(0.7, 0.85, 1);
  const dx = 0.7 / directionLength, dy = 0.85 / directionLength, dz = 1 / directionLength;
  const horizontal = Math.hypot(dx, dz);
  let distance = 0;
  for (const x of [-10.5, 10.5]) for (const y of [-1.35, 1.8]) for (const z of [-6.5, 6.5]) {
    const right = (x * dz - z * dx) / horizontal;
    const up = (-x * dx * dy - z * dz * dy) / horizontal + y * horizontal;
    const depth = x * dx + y * dy + z * dz;
    distance = Math.max(distance, depth + Math.max(Math.abs(right) / aspect, Math.abs(up)) / Math.tan(Math.PI / 8));
  }
  return distance * 1.08;
}
