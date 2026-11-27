import { add } from "./calc";
test("adds", () => {
  // formatting only
  expect(add(1, 2)).toBe(3);
});
