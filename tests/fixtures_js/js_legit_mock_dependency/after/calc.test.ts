import { vi } from "vitest";
import { add } from "./calc";
vi.mock("./db");
test("adds", () => {
  expect(add(1, 2)).toBe(3);
});
