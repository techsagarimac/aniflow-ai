import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "./Primitives";
import { canManage, labelize } from "../../utils/format";

describe("format helpers", () => {
  it("labelizes production stages", () => {
    expect(labelize("key_animation")).toBe("Key Animation");
  });
  it("restricts project management to managers", () => {
    expect(canManage("artist")).toBe(false);
    expect(canManage("production_manager")).toBe(true);
  });
});

describe("Badge", () => {
  it("renders status text", () => {
    render(<Badge tone="bad">high</Badge>);
    expect(screen.getByText("high")).toBeInTheDocument();
  });
});
