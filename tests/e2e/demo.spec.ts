import { expect, test } from "@playwright/test";

test("reviewer can enter the seeded portfolio and inspect analytics", async ({ page }) => {
  await page.goto("/");
  await page.screenshot({ path: "docs/screenshots/login.png", fullPage: true });
  await page.getByRole("button", { name: /enter demo workspace/i }).click();
  await expect(page.getByRole("heading", { name: "Clarity behind every position." })).toBeVisible();
  await expect(page.getByText("Performance vs. benchmark")).toBeVisible();
  await page.screenshot({ path: "docs/screenshots/dashboard.png", fullPage: true });
  await page.getByRole("button", { name: "Scenarios" }).click();
  await page.getByRole("button", { name: /run scenario/i }).click();
  await expect(page.getByText("ESTIMATED IMPACT")).toBeVisible();
  await page.screenshot({ path: "docs/screenshots/scenario.png", fullPage: true });
});
