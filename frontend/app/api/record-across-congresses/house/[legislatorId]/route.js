import "server-only";

import { NextResponse } from "next/server";

import { sanitizeRecordAcrossResponse } from "../../../../../lib/recordAcrossCongresses.mjs";

const BACKEND_BASE_URL =
  process.env.INTERNAL_BACKEND_API_BASE_URL ||
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

const INTERNAL_API_TOKEN_HEADER = "X-Internal-API-Token";

export async function GET(_request, context) {
  const params = await context.params;
  const legislatorId = params?.legislatorId;
  const token = process.env.INTERNAL_API_TOKEN;

  if (!token || !token.trim()) {
    return NextResponse.json({ detail: "Record unavailable" }, { status: 503 });
  }

  if (!legislatorId) {
    return NextResponse.json({ detail: "Record unavailable" }, { status: 404 });
  }

  try {
    const backendResponse = await fetch(
      `${BACKEND_BASE_URL}/internal/record-across-congresses/house/${encodeURIComponent(legislatorId)}`,
      {
        cache: "no-store",
        headers: {
          [INTERNAL_API_TOKEN_HEADER]: token,
        },
      },
    );

    if (!backendResponse.ok) {
      return NextResponse.json(
        { detail: "Record unavailable" },
        { status: backendResponse.status === 404 ? 404 : 502 },
      );
    }

    const sanitized = sanitizeRecordAcrossResponse(await backendResponse.json());
    if (!sanitized) {
      return NextResponse.json({ detail: "Record unavailable" }, { status: 502 });
    }

    return NextResponse.json(sanitized, {
      status: 200,
      headers: {
        "Cache-Control": "no-store",
      },
    });
  } catch (_error) {
    return NextResponse.json({ detail: "Record unavailable" }, { status: 502 });
  }
}
