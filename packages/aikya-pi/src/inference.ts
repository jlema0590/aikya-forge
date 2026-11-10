/** No provider execution in the read-only preview, including native UI helpers. */
export function lockInference<T extends object>(runtime: T): T {
  const operations = ["stream", "complete", "streamSimple", "completeSimple", "streamDeferred",
    "fetchDeferred", "generateImages", "classify"];
  return Object.assign(runtime, Object.fromEntries(operations.map((name) => [name, () => {
    throw new Error("Model execution is disabled in the Aikya read-only preview");
  }])));
}
