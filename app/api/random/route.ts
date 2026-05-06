import { NextResponse } from "next/server";
import { randomInt } from "crypto";
import { hasAccess } from "../../lib/payments";

export const runtime = "nodejs";

type RandomRequest = {
  accessToken?: string;
};

export async function POST(request: Request) {
  const body = (await request.json()) as RandomRequest;
  if (!hasAccess(body.accessToken)) {
    return NextResponse.json(
      { error: "A verified Solana payment is required before generating numbers." },
      { status: 403 },
    );
  }

  return NextResponse.json({ value: randomInt(0, 1001) });
}
