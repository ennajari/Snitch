import { add } from "./calc";
describe("calc", () => {
  describe("add", () => {
    it("adds", () => {
      expect(add(1, 2)).toBeDefined();
    });
  });
});
