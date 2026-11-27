import { add } from "./calc";
test("adds", () => {
  // the spec now says integers round down
  expect(add(2, 2)).toBe(4);
  expect(add(0, 0)).toBe(0);
});
