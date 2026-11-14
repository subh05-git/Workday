const crypto = require("node:crypto");

function verifySignature(rawBody, signatureHex, secret) {
  if (!rawBody || !signatureHex || !secret) return false;
  const expected = crypto.createHmac("sha256", secret).update(rawBody, "utf8").digest("hex");
  const a = Buffer.from(expected, "hex");
  const b = Buffer.from(signatureHex, "hex");
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

function normalizeWorkdayEvent(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Invalid Workday webhook payload");
  }
  const eventId = payload.eventId || payload.wid || null;
  if (!eventId) {
    throw new Error("Missing eventId or wid");
  }
  return {
    eventId: String(eventId),
    tenant: String(payload.tenant || "unknown"),
    integrationName: String(payload.integrationSystem || payload.source || "unspecified"),
    status: String(payload.status || "UNKNOWN").toUpperCase(),
    recordsProcessed: Number(payload.recordsProcessed || 0),
    occurredAtUtc: payload.timestamp ? new Date(payload.timestamp).toISOString() : null,
  };
}

module.exports = { verifySignature, normalizeWorkdayEvent };
