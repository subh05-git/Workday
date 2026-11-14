import test from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { verifySignature, normalizeWorkdayEvent } = require("../src/js/webhook_normalizer.js");

test("verifySignature validates HMAC-SHA256", () => {
  const secret = "wd_secret_123";
  const body = JSON.stringify({ eventId: "EVT-1", status: "completed" });
  const sig = crypto.createHmac("sha256", secret).update(body, "utf8").digest("hex");
  assert.equal(verifySignature(body, sig, secret), true);
  assert.equal(verifySignature(body, "00".repeat(32), secret), false);
});

test("normalizeWorkdayEvent standardizes fields", () => {
  const out = normalizeWorkdayEvent({
    wid: "WD-998",
    tenant: "acme_prod",
    integrationSystem: "INT001_Import_Journal_Entries",
    status: "completed",
    recordsProcessed: "4200",
    timestamp: "2026-11-14T12:00:00Z",
  });
  assert.equal(out.eventId, "WD-998");
  assert.equal(out.status, "COMPLETED");
  assert.equal(out.recordsProcessed, 4200);
});
