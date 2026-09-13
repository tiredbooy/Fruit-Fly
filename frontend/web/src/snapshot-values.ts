/** Strict JSON boundary primitives shared by versioned telemetry parsers. */
export type UnknownRecord = Record<string, unknown>;

export function parseNumbers<K extends string>(value: unknown, keys: readonly K[], label: string): Record<K, number> {
  const record = asRecord(value, label);
  exactKeys(record, keys);
  return Object.fromEntries(keys.map((key) => [key, asNumber(field(record, key), `${label}.${key}`)])) as Record<K, number>;
}
export function asRecord(value: unknown, label: string): UnknownRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${label} must be an object`);
  return value as UnknownRecord;
}
export function field(record: UnknownRecord, key: string): unknown {
  if (!Object.hasOwn(record, key)) throw new Error(`Missing ${key}`);
  return record[key];
}
export function exactKeys(record: UnknownRecord, expected: readonly string[]): void {
  const actual = Object.keys(record).sort(), required = [...expected].sort();
  if (actual.length !== required.length || actual.some((key, index) => key !== required[index])) throw new Error("Message fields do not match the schema");
}
export function asNumber(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${label} must be finite`);
  return value;
}
export function asInteger(value: unknown, label: string): number {
  const number = asNumber(value, label);
  if (!Number.isSafeInteger(number)) throw new Error(`${label} must be an integer`);
  return number;
}
export function asString(value: unknown, label: string): string {
  if (typeof value !== "string") throw new Error(`${label} must be text`);
  return value;
}
export function asBoolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") throw new Error(`${label} must be boolean`);
  return value;
}
