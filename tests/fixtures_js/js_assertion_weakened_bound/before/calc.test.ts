import { add } from "./calc";
test("small error", () => {
  const err = Math.abs(add(1, 2) - 3);
  expect(err).toBeLessThan(0.01);
});
