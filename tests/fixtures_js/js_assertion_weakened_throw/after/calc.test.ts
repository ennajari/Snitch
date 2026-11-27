import { add } from "./calc";
test("throws", () => {
  expect(() => add(NaN, 1)).toThrow();
});
