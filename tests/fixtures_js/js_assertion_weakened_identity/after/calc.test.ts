import { add } from "./calc";
test("same object", () => {
  expect(cache.get(1)).toEqual(cached);
});
