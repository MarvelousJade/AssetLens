import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  fullyParallel: true,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command:
        "python -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8765",
      url: "http://127.0.0.1:8765/api/health",
      reuseExistingServer: true,
    },
    {
      command: "npm --prefix apps/web run dev -- --hostname 127.0.0.1",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: true,
      env: {
        API_UPSTREAM: "http://127.0.0.1:8765",
      },
    },
  ],
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
