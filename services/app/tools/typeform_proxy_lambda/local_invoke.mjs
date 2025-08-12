// Minimal local runner to exercise the proxy handler without AWS
import { handler } from "./index.mjs";

async function main() {
    if (!process.env.TYPEFORM_API_KEY) {
        console.error("Please set TYPEFORM_API_KEY in your environment before running.");
        process.exit(1);
    }
    const event = {
        method: "GET",
        path: "/forms/FAKE_FORM_ID", // replace with a real form id to test against live API
        query: {},
        headers: { "x-correlation-id": "localtest" },
    };
    const res = await handler(event);
    console.log("status:", res.statusCode);
    console.log("headers:", res.headers);
    console.log("body:", res.body?.slice(0, 200));
}

main().catch((e) => {
    console.error(e);
    process.exit(1);
});


