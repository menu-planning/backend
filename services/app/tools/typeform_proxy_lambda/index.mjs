import { fetch } from "undici";

const TYPEFORM_API_KEY = process.env.TYPEFORM_API_KEY;
const TYPEFORM_BASE_URL = process.env.TYPEFORM_BASE_URL || "https://api.typeform.com";
const REQUEST_TIMEOUT_MS = Number(process.env.TYPEFORM_TIMEOUT_MS || 15000);

const MAX_REQUEST_BODY_BYTES = 128 * 1024; // 128KB
const MAX_RESPONSE_BODY_BYTES = 1024 * 1024; // 1MB

// Strict allowlist: only endpoints used by our client today
// - GET /forms/{id}
// - GET /forms/{id}/webhooks
// - GET /forms/{id}/webhooks/{tag}
// - PUT /forms/{id}/webhooks/{tag}
// - DELETE /forms/{id}/webhooks/{tag}
const PATH_ALLOWLIST = {
    GET: [
        /^\/forms\/[^/]+$/,
        /^\/forms\/[^/]+\/webhooks$/, // list webhooks
        /^\/forms\/[^/]+\/webhooks\/[^/]+$/, // get webhook
    ],
    PUT: [/^\/forms\/[^/]+\/webhooks\/[^/]+$/],
    DELETE: [/^\/forms\/[^/]+\/webhooks\/[^/]+$/],
};

function isMethodAllowed(method) {
    return Object.prototype.hasOwnProperty.call(PATH_ALLOWLIST, method);
}

function isPathAllowed(method, path) {
    const patterns = PATH_ALLOWLIST[method] || [];
    return patterns.some((re) => re.test(path));
}

function bytesLength(value) {
    return Buffer.byteLength(typeof value === "string" ? value : String(value), "utf8");
}

function buildUrl(baseUrl, path, query) {
    // Ensure leading slash
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    const url = new URL(normalizedPath, baseUrl);
    if (query && typeof query === "object") {
        for (const [key, rawVal] of Object.entries(query)) {
            if (rawVal === undefined || rawVal === null) continue;
            const values = Array.isArray(rawVal) ? rawVal : [rawVal];
            for (const v of values) url.searchParams.append(key, String(v));
        }
    }
    return url;
}

function sanitizeOutboundHeaders(inboundHeaders = {}) {
    const headers = {};
    const lower = {};
    for (const [k, v] of Object.entries(inboundHeaders || {})) lower[String(k).toLowerCase()] = v;

    const allowedForward = [
        "content-type",
        "if-none-match",
        "if-match",
        "user-agent",
        "accept",
    ];
    for (const name of allowedForward) {
        if (lower[name] !== undefined) headers[name] = lower[name];
    }

    // Enforce our auth header
    headers["authorization"] = `Bearer ${TYPEFORM_API_KEY}`;
    if (!headers["accept"]) headers["accept"] = "application/json";
    return headers;
}

function pickResponseHeaders(res) {
    const passThrough = [
        "content-type",
        "etag",
        "retry-after",
        "x-rate-limit-limit",
        "x-rate-limit-remaining",
    ];
    const out = {};
    for (const name of passThrough) {
        const val = res.headers.get(name);
        if (val !== null) out[name] = val;
    }
    return out;
}

function log(level, message, extra = {}) {
    const entry = {
        level,
        message,
        ts: new Date().toISOString(),
        ...extra,
    };
    // eslint-disable-next-line no-console
    console.log(JSON.stringify(entry));
}

export async function handler(event) {
    const start = Date.now();
    const correlationId = event?.correlation_id || event?.correlationId || event?.headers?.["x-correlation-id"] || null;

    try {
        if (!TYPEFORM_API_KEY) {
            throw Object.assign(new Error("TYPEFORM_API_KEY not configured"), { category: "config" });
        }

        const method = String(event?.method || "").toUpperCase();
        const path = String(event?.path || "");
        const query = event?.query || {};
        const inboundHeaders = event?.headers || {};
        let body = event?.body;

        if (!method || !path) {
            throw Object.assign(new Error("method and path are required"), { category: "validation" });
        }
        if (!isMethodAllowed(method) || !isPathAllowed(method, path)) {
            throw Object.assign(new Error("method/path not allowed"), { category: "not_allowed" });
        }

        if (body !== undefined && body !== null) {
            if (typeof body !== "string") body = JSON.stringify(body);
            const size = bytesLength(body);
            if (size > MAX_REQUEST_BODY_BYTES) {
                throw Object.assign(new Error("request body too large"), { category: "request_too_large" });
            }
        }

        const url = buildUrl(TYPEFORM_BASE_URL, path, query);
        const headers = sanitizeOutboundHeaders(inboundHeaders);

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        let res;
        try {
            res = await fetch(url, {
                method,
                headers,
                body: method === "GET" || method === "HEAD" ? undefined : body,
                signal: controller.signal,
            });
        } finally {
            clearTimeout(timer);
        }

        const respHeaders = pickResponseHeaders(res);
        const contentLengthHeader = res.headers.get("content-length");
        if (contentLengthHeader && Number(contentLengthHeader) > MAX_RESPONSE_BODY_BYTES) {
            log("warn", "response too large (content-length)", {
                correlation_id: correlationId,
                method,
                url: String(url),
                content_length: Number(contentLengthHeader),
            });
            return {
                statusCode: 502,
                headers: { "content-type": "application/json" },
                body: JSON.stringify({ message: "Upstream response too large" }),
            };
        }

        const text = await res.text();
        if (bytesLength(text) > MAX_RESPONSE_BODY_BYTES) {
            log("warn", "response too large (after read)", {
                correlation_id: correlationId,
                method,
                url: String(url),
                body_length: bytesLength(text),
            });
            return {
                statusCode: 502,
                headers: { "content-type": "application/json" },
                body: JSON.stringify({ message: "Upstream response too large" }),
            };
        }

        const durMs = Date.now() - start;
        log("info", "proxy request completed", {
            correlation_id: correlationId,
            method,
            url: String(url),
            statusCode: res.status,
            dur_ms: durMs,
        });

        return {
            statusCode: res.status,
            headers: respHeaders,
            body: text,
        };
    } catch (err) {
        const durMs = Date.now() - start;
        const category = err?.category || (err?.name === "AbortError" ? "timeout" : "error");
        log("error", "proxy request failed", {
            correlation_id: correlationId,
            err_category: category,
            error: String(err?.message || err),
            dur_ms: durMs,
        });
        const statusCode = category === "not_allowed" ? 403 : category === "validation" ? 400 : category === "request_too_large" ? 413 : category === "timeout" ? 504 : category === "config" ? 500 : 502;
        return {
            statusCode,
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ message: "Proxy error", category, error: String(err?.message || err) }),
        };
    }
}


