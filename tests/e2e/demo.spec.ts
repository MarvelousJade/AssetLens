import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";

test("reviewer can enter the seeded portfolio and inspect analytics", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.screenshot({ path: testInfo.outputPath("login.png"), fullPage: true });
  await page.getByRole("button", { name: /enter demo workspace/i }).click();
  await expect(page.getByRole("heading", { name: "Clarity behind every position." })).toBeVisible();
  await expect(page.getByText("Performance vs. benchmark")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("dashboard.png"), fullPage: true });
  await page.getByRole("button", { name: "Scenarios" }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.getByRole("button", { name: /run scenario/i }).click();
  await expect(page.getByText("ESTIMATED IMPACT")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("scenario.png") });
});

test("reviewer can create, import, and download a portfolio report", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.getByRole("button", { name: /enter demo workspace/i }).click();
  await expect(page.getByText("Performance vs. benchmark")).toBeVisible();
  await page.getByRole("button", { name: "Holdings" }).click();
  await page.getByPlaceholder("Portfolio name").fill("Browser import portfolio");
  await page.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page.getByText("No holdings yet. Import a CSV to get started.")).toBeVisible();
  await expect(page.getByRole("combobox", { name: "PORTFOLIO" })).toContainText("Browser import portfolio");
  await expect(page.getByRole("button", { name: "Export report" })).toBeDisabled();
  await page.getByLabel("Choose CSV file").setInputFiles({
    name: "holdings.csv", mimeType: "text/csv",
    buffer: Buffer.from("ticker,quantity,average_cost,current_price\nBROWSER,2,10,12\n"),
  });
  await expect(page.getByText("1 holdings imported atomically.")).toBeVisible();
  await expect(page.getByRole("cell", { name: /BROWSER/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "Export report" })).toBeEnabled();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Export report" }).click(),
  ]);
  expect(await download.failure()).toBeNull();
  const reportPath = testInfo.outputPath("imported-portfolio.pdf");
  await download.saveAs(reportPath);
  const content = await readFile(reportPath);
  expect(content.subarray(0, 4).toString()).toBe("%PDF");
  expect(content.length).toBeGreaterThan(2000);
});
