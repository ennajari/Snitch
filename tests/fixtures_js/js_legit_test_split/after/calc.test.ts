import { add } from "./calc";
test("adds", () => {
  expect(add(1, 2)).toBe(3);
});
test("adds negatives", () => {
  expect(add(-1, 1)).toBe(0);
});
