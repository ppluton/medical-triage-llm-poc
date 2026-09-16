const MAX_BODY_BYTES = 32 * 1024;
import {
  bearerToken,
  jsonResponse,
  modalUrl,
  upstreamHeaders,
  verifyToken,
} from "../_shared.js";

async function readBoundedBody(request) {
  if (!request.body) return new Uint8Array();
  const reader = request.body.getReader();
  const chunks = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > MAX_BODY_BYTES) {
      await reader.cancel();
      throw new Error("body_too_large");
    }
    chunks.push(value);
  }
  const body = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.DEMO_ACCESS_TOKEN || !env.MODAL_API_TOKEN || !env.MODAL_API_URL) {
    return jsonResponse(503, "Demonstration backend is not configured");
  }

  const provided = bearerToken(request);
  if (!(await verifyToken(provided, env.DEMO_ACCESS_TOKEN))) {
    return jsonResponse(401, "Unauthorized");
  }

  const contentType = request.headers.get("Content-Type") || "";
  if (!contentType.toLowerCase().startsWith("application/json")) {
    return jsonResponse(415, "Content-Type must be application/json");
  }
  const contentLength = Number(request.headers.get("Content-Length") || "0");
  if (!Number.isFinite(contentLength) || contentLength > MAX_BODY_BYTES) {
    return jsonResponse(413, "Request body is too large");
  }

  let body;
  try {
    body = await readBoundedBody(request);
  } catch {
    return jsonResponse(413, "Request body is too large");
  }

  let target;
  try {
    target = modalUrl(env.MODAL_API_URL, "/v1/triage");
  } catch {
    return jsonResponse(503, "Demonstration backend is not configured");
  }

  try {
    const upstream = await fetch(target, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.MODAL_API_TOKEN}`,
        "Content-Type": "application/json",
      },
      body,
      redirect: "error",
    });
    const headers = upstreamHeaders(
      upstream.headers.get("Content-Type") || "application/json",
    );
    return new Response(upstream.body, { status: upstream.status, headers });
  } catch {
    return jsonResponse(502, "Demonstration backend is temporarily unavailable");
  }
}

export function onRequest() {
  return jsonResponse(405, "Method not allowed");
}
