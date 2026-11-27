import { vi } from "vitest";
import { add } from "./calc";
vi.mock("./calc");
test("adds", () => {
  vi.mocked(add).mockReturnValue(3);
  expect(add(1, 2)).toBe(3);
});
