"use client";

import { useMemo, useState } from "react";
import { Transaction } from "@solana/web3.js";
import { useConnection, useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { Buffer } from "buffer";

type InvoiceResponse = {
  wallet: string;
  amount: number;
  memo: number;
  startTime: number;
  endTime: number;
  invoiceId: string;
  invoiceToken: string;
  transaction: string;
  agentMint: string;
  currencyMint: string;
};

type VerifyResponse = {
  verified: true;
  accessToken: string;
  expiresAt: number;
};

async function postJson<TResponse>(url: string, body: unknown): Promise<TResponse> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error ?? "Request failed.");
  }
  return payload as TResponse;
}

async function signAndSendPayment(
  txBase64: string,
  signTransaction: (transaction: Transaction) => Promise<Transaction>,
  connection: ReturnType<typeof useConnection>["connection"],
) {
  const transaction = Transaction.from(Buffer.from(txBase64, "base64"));
  const signedTransaction = await signTransaction(transaction);
  const signature = await connection.sendRawTransaction(signedTransaction.serialize(), {
    skipPreflight: false,
    preflightCommitment: "confirmed",
  });

  const latestBlockhash = await connection.getLatestBlockhash("confirmed");
  await connection.confirmTransaction({ signature, ...latestBlockhash }, "confirmed");

  return signature;
}

export default function RandomGate() {
  const { connection } = useConnection();
  const { connected, publicKey, signTransaction } = useWallet();
  const [invoice, setInvoice] = useState<InvoiceResponse | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<number | null>(null);
  const [signature, setSignature] = useState<string | null>(null);
  const [randomNumber, setRandomNumber] = useState<number | null>(null);
  const [status, setStatus] = useState("Connect a Solana wallet to begin.");
  const [isBusy, setIsBusy] = useState(false);

  const priceLabel = useMemo(() => {
    if (!invoice) return "0.1 SOL";
    return `${invoice.amount / 1_000_000_000} SOL`;
  }, [invoice]);

  async function handleCreateInvoice() {
    if (!publicKey) return;
    setIsBusy(true);
    setRandomNumber(null);
    setAccessToken(null);
    setSignature(null);
    try {
      setStatus("Creating a unique on-chain invoice...");
      const nextInvoice = await postJson<InvoiceResponse>("/api/payment/invoice", {
        wallet: publicKey.toBase58(),
      });
      setInvoice(nextInvoice);
      setStatus("Invoice ready. Review and sign the payment in your wallet.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to create invoice.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handlePayAndVerify() {
    if (!invoice || !signTransaction) return;
    setIsBusy(true);
    try {
      setStatus("Awaiting wallet signature...");
      const nextSignature = await signAndSendPayment(
        invoice.transaction,
        signTransaction,
        connection,
      );
      setSignature(nextSignature);
      setStatus("Transaction confirmed. Verifying invoice on the backend (this can take a few seconds)...");

      const verification = await postJson<VerifyResponse>("/api/payment/verify", {
        invoiceId: invoice.invoiceId,
        invoiceToken: invoice.invoiceToken,
        wallet: invoice.wallet,
        signature: nextSignature,
      });
      setAccessToken(verification.accessToken);
      setExpiresAt(verification.expiresAt);
      setStatus("Payment verified. Random number generation is unlocked.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to verify payment.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleGenerateRandomNumber() {
    if (!accessToken) return;
    setIsBusy(true);
    try {
      const result = await postJson<{ value: number }>("/api/random", { accessToken });
      setRandomNumber(result.value);
      setStatus("Generated a fresh server-side random number.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to generate number.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Solana-gated utility</p>
        <h1>Pay {priceLabel}, unlock random numbers.</h1>
        <p>
          Connect a wallet, sign a pump.fun tokenized-agent invoice transaction,
          and let the backend verify the on-chain payment before generating a
          random number from 0 through 1000.
        </p>
        <WalletMultiButton />
      </section>

      <section className="card">
        <div className="steps">
          <div className={connected ? "step done" : "step"}>1. Wallet connected</div>
          <div className={invoice ? "step done" : "step"}>2. Invoice created</div>
          <div className={accessToken ? "step done" : "step"}>3. Payment verified</div>
        </div>

        <p className="status">{status}</p>

        <div className="actions">
          <button onClick={handleCreateInvoice} disabled={!connected || isBusy}>
            Create invoice
          </button>
          <button onClick={handlePayAndVerify} disabled={!invoice || !signTransaction || isBusy}>
            Sign, pay, and verify
          </button>
          <button onClick={handleGenerateRandomNumber} disabled={!accessToken || isBusy}>
            Generate number
          </button>
        </div>

        {invoice && (
          <dl className="details">
            <div><dt>Invoice PDA</dt><dd>{invoice.invoiceId}</dd></div>
            <div><dt>Agent mint</dt><dd>{invoice.agentMint}</dd></div>
            <div><dt>Currency mint</dt><dd>{invoice.currencyMint}</dd></div>
            <div><dt>Memo</dt><dd>{invoice.memo}</dd></div>
            <div><dt>Valid until</dt><dd>{new Date(invoice.endTime * 1000).toLocaleString()}</dd></div>
            {signature && <div><dt>Signature</dt><dd>{signature}</dd></div>}
            {expiresAt && <div><dt>Access expires</dt><dd>{new Date(expiresAt).toLocaleString()}</dd></div>}
          </dl>
        )}

        <div className="result" aria-live="polite">
          {randomNumber ?? "—"}
        </div>
      </section>
    </main>
  );
}
