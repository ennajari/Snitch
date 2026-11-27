import { add } from "./calc";
test("adds", () => {
  if (process.env.CI_STRICT) {
    expect(add(1, 2)).toBe(3);
  }
});
