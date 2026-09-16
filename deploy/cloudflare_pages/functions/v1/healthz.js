import {
  bearerToken,
  jsonResponse,
  modalUrl,
  upstreamHeaders,
  verifyToken,
} from "../_shared.js";

export async function onRequestGet({ request, env }) {
  if (!env.DEMO_ACCESS_TOKEN || !env.MODAL_API_TOKEN || !env.MODAL_API_URL) {
    return jsonResponse(503, "Demonstration backend is not configured");
  }
  if (!(await verifyToken(bearerToken(request), env.DEMO_ACCESS_TOKEN))) {
    return jsonResponse(401, "Unauthorized");
  }

  let target;
  try {
    target = modalUrl(env.MODAL_API_URL, "/healthz");
  } catch {
    return jsonResponse(503, "Demonstration backend is not configured");
  }

  try {
    const upstream = await fetch(target, {
      headers: { Authorization: `Bearer ${env.MODAL_API_TOKEN}` },
      redirect: "error",
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: upstreamHeaders(
        upstream.headers.get("Content-Type") || "application/json",
      ),
    });
  } catch {
    return jsonResponse(502, "Demonstration backend is temporarily unavailable");
  }
}

export function onRequest() {
  return jsonResponse(405, "Method not allowed");
}
