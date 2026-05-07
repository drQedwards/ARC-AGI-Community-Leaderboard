import { NextResponse } from "next/server";
import {
  getIssuedInvoice,
  grantAccess,
  markInvoiceVerified,
  verifyInvoicePayment,
} from "../../../lib/payments";

export const runtime = "nodejs";

type VerifyRequest = {
  invoiceId?: string;
  invoiceToken?: string;
  wallet?: string;
  signature?: string;
};

function parseInvoiceId(body: VerifyRequest) {
  if (!body.invoiceId) {
    throw new Error("Invoice ID is required.");
  }
  if (!body.invoiceToken) {
    throw new Error("Invoice token is required.");
  }
  return body.invoiceId;
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
    const invoiceId = parseInvoiceId(body);
    const invoice = getIssuedInvoice(invoiceId, body.invoiceToken);

    if (!invoice) {
      return NextResponse.json(
        { error: "Invoice is unknown or expired. Please create a new invoice." },
        { status: 404 },
      );
    }

    if (body.wallet && body.wallet !== invoice.wallet) {
      return NextResponse.json(
        { error: "Wallet does not match the issued invoice." },
        { status: 400 },
      );
    }

    if (invoice.verifiedAt) {
      return NextResponse.json(
        { error: "Invoice has already been used. Please create a new invoice." },
        { status: 409 },
      );
    }
    const invoice = parseInvoice(body);

    const paid = await verifyInvoicePayment(invoice);
    if (!paid) {
      return NextResponse.json(
        { error: "Payment has not been verified on-chain yet." },
        { status: 402 },
      );
    }

    markInvoiceVerified(invoiceId);

    return NextResponse.json({
      verified: true,
      signature: body.signature,
      invoiceId,
      ...grantAccess(invoice.wallet),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to verify payment.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
