import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConfidenceBadge } from "./ConfidenceBadge";

describe("ConfidenceBadge", () => {
  it("renders the confidence as a rounded percentage", () => {
    render(<ConfidenceBadge confidence={0.873} />);

    expect(screen.getByText("87% confidence")).toBeInTheDocument();
  });

  it("uses the high-confidence tone at or above 70%", () => {
    render(<ConfidenceBadge confidence={0.7} />);

    expect(screen.getByText("70% confidence")).toHaveClass("bg-emerald-100");
  });

  it("uses the low-confidence tone below 40%", () => {
    render(<ConfidenceBadge confidence={0.1} />);

    expect(screen.getByText("10% confidence")).toHaveClass("bg-rose-100");
  });
});
