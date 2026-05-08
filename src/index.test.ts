import { expect, test } from "bun:test";

import { sloppyTron } from "./index.js";

test("exports project metadata", () => {
  expect(sloppyTron.name).toBe("sloppy-tron");
  expect(sloppyTron.providerId).toBe("body");
});
