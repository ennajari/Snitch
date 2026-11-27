import { add } from "./calc";
test("adds", () => { expect(add(1, 2)).toBe(3); });
test("subtracts", () => { expect(add(2, 1)).toBe(3); });
