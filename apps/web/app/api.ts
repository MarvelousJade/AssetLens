export const DEMO_TOKEN = "assetlens-demo-token";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token = DEMO_TOKEN,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...options, headers, cache: "no-store" });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      message =
        typeof payload.detail === "string"
          ? payload.detail
          : JSON.stringify(payload.detail ?? payload);
    } catch {
      // Preserve the HTTP status when the response is not JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function downloadReport(reportId: string, token = DEMO_TOKEN) {
  const response = await fetch(`/api/reports/${reportId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Report download failed.");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `assetlens-report-${reportId.slice(0, 8)}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}
