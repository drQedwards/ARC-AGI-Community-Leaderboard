import { NextResponse } from "next/server";
import { PublicKey } from "@solana/web3.js";
import { getPublicConfig, issuePaymentInvoice } from "../../../lib/payments";

export const runtime = "nodejs";

type InvoiceRequest = {
  wallet?: string;
};

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as InvoiceRequest;
    if (!body.wallet) {
      return NextResponse.json({ error: "Wallet address is required." }, { status: 400 });
    }

    const wallet = new PublicKey(body.wallet).toBase58();
    const invoice = await issuePaymentInvoice(wallet);

    return NextResponse.json({
      ...getPublicConfig(),
      ...invoice,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to create invoice.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
