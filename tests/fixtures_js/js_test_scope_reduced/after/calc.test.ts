import { add } from "./calc";
test("many cases", () => {
  for (let i = 0; i < 100; i++) {
    expect(add(i, 0)).toBe(i);
  }
});
