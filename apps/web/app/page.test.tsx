import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import Home from "./page";

describe("AssetLens entry", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("offers a zero-setup demo workspace", async () => {
    render(<Home />);
    expect(await screen.findByText("Explore AssetLens")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /enter demo workspace/i }));
    expect(localStorage.getItem("assetlens-token")).toBe("assetlens-demo-token");
  });
});
