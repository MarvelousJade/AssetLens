import { existsSync, mkdirSync } from "node:fs";
import { defineConfig, devices } from "@playwright/test";

const localPython = process.platform === "win32"
  ? "apps/api/.venv/Scripts/python.exe"
  : "apps/api/.venv/bin/python";
const apiPython = process.env.API_PYTHON ?? (existsSync(localPython) ? localPython : "python");
mkdirSync(".tmp", { recursive: true });

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  fullyParallel: true,
  use: {
    baseURL: "http://127.0.0.1:3101",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: `"${apiPython}" -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8876`,
      url: "http://127.0.0.1:8876/api/health",
      reuseExistingServer: false,
      env: {
        DATABASE_URL: `sqlite:///./.tmp/assetlens-e2e-${process.pid}.db`,
        COPILOT_PROVIDER: "deterministic",
        TASK_MODE: "local",
        DEMO_TOKEN: "assetlens-demo-token",
      },
    },
    {
      command: "npm --prefix apps/web run dev -- --hostname 127.0.0.1 --port 3101",
      url: "http://127.0.0.1:3101",
      reuseExistingServer: false,
      env: { API_UPSTREAM: "http://127.0.0.1:8876" },
    },
  ],
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
