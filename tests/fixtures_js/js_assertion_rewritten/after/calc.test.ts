import { add } from "./calc";
test("one hour", () => {
  expect(hours(3600) * 60).toBe(1);
});
