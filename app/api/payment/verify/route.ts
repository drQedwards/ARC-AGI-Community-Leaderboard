import { NextResponse } from "next/server";
import { grantAccess, InvoicePayload, verifyInvoicePayment } from "../../../lib/payments";

export const runtime = "nodejs";

type VerifyRequest = InvoicePayload & {
  signature?: string;
};

function assertSafePositiveInteger(value: number, name: string) {
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new Error(`${name} must be a positive safe integer.`);
  }
}

function parseInvoice(body: VerifyRequest): InvoicePayload {
  const invoice = {
    wallet: body.wallet,
    amount: Number(body.amount),
    memo: Number(body.memo),
    startTime: Number(body.startTime),
    endTime: Number(body.endTime),
  };

  if (!invoice.wallet) {
    throw new Error("Wallet address is required.");
  }
  assertSafePositiveInteger(invoice.amount, "amount");
  assertSafePositiveInteger(invoice.memo, "memo");
  assertSafePositiveInteger(invoice.startTime, "startTime");
  assertSafePositiveInteger(invoice.endTime, "endTime");
  if (invoice.endTime <= invoice.startTime) {
    throw new Error("endTime must be greater than startTime.");
  }

  return invoice;
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as VerifyRequest;
    const invoice = parseInvoice(body);

    const paid = await verifyInvoicePayment(invoice);
    if (!paid) {
      return NextResponse.json(
        { error: "Payment has not been verified on-chain yet." },
        { status: 402 },
      );
    }

    return NextResponse.json({
      verified: true,
      signature: body.signature,
      ...grantAccess(invoice.wallet),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to verify payment.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
