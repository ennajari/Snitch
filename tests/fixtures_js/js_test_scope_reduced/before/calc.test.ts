import { add } from "./calc";
test("many cases", () => {
  for (let i = 0; i < 20000; i++) {
    expect(add(i, 0)).toBe(i);
  }
});
