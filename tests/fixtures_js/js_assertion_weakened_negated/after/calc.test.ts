import { add } from "./calc";
test("adds", () => {
  expect(add(1, 2)).not.toBe(3);
});
