const encoder = new TextEncoder();

export function jsonResponse(status, detail) {
  return Response.json(
    { detail },
    {
      status,
      headers: {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      },
    },
  );
}

export async function verifyToken(provided, expected) {
  const [providedHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(provided)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected)),
  ]);
  return crypto.subtle.timingSafeEqual(providedHash, expectedHash);
}

export function bearerToken(request) {
  const authorization = request.headers.get("Authorization") || "";
  return authorization.startsWith("Bearer ") ? authorization.slice(7) : "";
}

export function modalUrl(value, path) {
  const target = new URL(value);
  const trustedModalHost = [".modal.run", ".modal.direct"].some((suffix) =>
    target.hostname.endsWith(suffix),
  );
  if (target.protocol !== "https:" || !trustedModalHost) {
    throw new Error("invalid_modal_origin");
  }
  return new URL(path, target).toString();
}

export function upstreamHeaders(contentType = "application/json") {
  return new Headers({
    "Cache-Control": "no-store",
    "Content-Type": contentType,
    "X-Content-Type-Options": "nosniff",
  });
}
