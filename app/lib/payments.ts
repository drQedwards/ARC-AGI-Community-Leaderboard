import { createHmac, randomBytes, timingSafeEqual } from "crypto";
import {
  getInvoiceIdPDA,
  PumpAgent,
} from "@pump-fun/agent-payments-sdk";
import { Connection, PublicKey, Transaction } from "@solana/web3.js";

export const SOL_DECIMALS = 9;
export const DEFAULT_INVOICE_TTL_SECONDS = 15 * 60;
export const ACCESS_TTL_MS = 60 * 60 * 1000;
export const PAYMENT_VERIFY_RETRY_ATTEMPTS = 10;
export const PAYMENT_VERIFY_RETRY_DELAY_MS = 2_000;

const TOKEN_VERSION = 1;

type InvoiceTokenPayload = InvoicePayload & {
  kind: "invoice";
  version: typeof TOKEN_VERSION;
  invoiceId: string;
};

type AccessTokenPayload = {
  kind: "access";
  version: typeof TOKEN_VERSION;
  wallet: string;
  expiresAt: number;
};

type IssuedInvoice = InvoicePayload & {
  invoiceId: string;
  invoiceToken: string;
  transaction: string;
  createdAt: number;
  verifiedAt?: number;
};

type GlobalPaymentState = typeof globalThis & {
  __rngIssuedInvoices?: Map<string, IssuedInvoice>;
};

export type InvoicePayload = {
  wallet: string;
  amount: number;
  memo: number;
  startTime: number;
  endTime: number;
};

export function getIssuedInvoices() {
  const state = globalThis as GlobalPaymentState;
  state.__rngIssuedInvoices ??= new Map<string, IssuedInvoice>();
  return state.__rngIssuedInvoices;
}

function pruneIssuedInvoices(nowSeconds = Math.floor(Date.now() / 1000)) {
  const invoices = getIssuedInvoices();
  for (const [invoiceId, invoice] of invoices) {
    if (invoice.endTime < nowSeconds) {
      invoices.delete(invoiceId);
    }
  }
}

function getRequiredEnv(name: string) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function getSigningSecret() {
  return getRequiredEnv("PAYMENT_SIGNING_SECRET");
}

function signTokenPayload(payload: InvoiceTokenPayload | AccessTokenPayload) {
  const encodedPayload = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const signature = createHmac("sha256", getSigningSecret())
    .update(encodedPayload)
    .digest("base64url");

  return `${encodedPayload}.${signature}`;
}

function verifyTokenPayload<TPayload>(token: string): TPayload | null {
  const [encodedPayload, signature, ...extraParts] = token.split(".");
  if (!encodedPayload || !signature || extraParts.length > 0) return null;

  const expectedSignature = createHmac("sha256", getSigningSecret())
    .update(encodedPayload)
    .digest("base64url");
  const provided = Buffer.from(signature);
  const expected = Buffer.from(expectedSignature);

  if (provided.length !== expected.length || !timingSafeEqual(provided, expected)) {
    return null;
  }

  try {
    return JSON.parse(Buffer.from(encodedPayload, "base64url").toString("utf8")) as TPayload;
  } catch {
    return null;
  }
}

function assertSafePositiveInteger(value: number, name: string) {
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new Error(`${name} must be a positive safe integer.`);
  }
}

function assertInvoicePayload(payload: InvoicePayload) {
  new PublicKey(payload.wallet);
  assertSafePositiveInteger(payload.amount, "amount");
  assertSafePositiveInteger(payload.memo, "memo");
  assertSafePositiveInteger(payload.startTime, "startTime");
  assertSafePositiveInteger(payload.endTime, "endTime");

  if (payload.endTime <= payload.startTime) {
    throw new Error("Invoice endTime must be greater than startTime.");
  }
}

function getPriceAmount() {
  const amount = Number(getRequiredEnv("PRICE_AMOUNT"));
  if (!Number.isSafeInteger(amount) || amount <= 0) {
    throw new Error("PRICE_AMOUNT must be a positive integer in the currency's smallest unit.");
  }
  return amount;
}

export function getPublicConfig() {
  return {
    amount: getPriceAmount(),
    agentMint: getRequiredEnv("AGENT_TOKEN_MINT_ADDRESS"),
    currencyMint: getRequiredEnv("CURRENCY_MINT"),
  };
}

export function getConnection() {
  return new Connection(getRequiredEnv("SOLANA_RPC_URL"), "confirmed");
}

export function getAgent(connection = getConnection()) {
  const agentMint = new PublicKey(getRequiredEnv("AGENT_TOKEN_MINT_ADDRESS"));
  return new PumpAgent(agentMint, "mainnet", connection);
}

export function createInvoiceParams(wallet: string): InvoicePayload {
  const now = Math.floor(Date.now() / 1000);
  const memoBuffer = randomBytes(6);
  const memo = memoBuffer.readUIntBE(0, 6);
  const startTime = now;
  const endTime = now + DEFAULT_INVOICE_TTL_SECONDS;

  const invoice = {
    wallet,
    amount: getPriceAmount(),
    memo,
    startTime,
    endTime,
  };
  assertInvoicePayload(invoice);

  return invoice;
}

function deriveInvoiceId(invoice: InvoicePayload) {
  const agentMint = new PublicKey(getRequiredEnv("AGENT_TOKEN_MINT_ADDRESS"));
  const currencyMint = new PublicKey(getRequiredEnv("CURRENCY_MINT"));

  const [invoiceId] = getInvoiceIdPDA(
    agentMint,
    currencyMint,
    invoice.amount,
    invoice.memo,
    invoice.startTime,
    invoice.endTime,
  );

  return invoiceId;
}

async function buildPaymentTransaction(invoice: InvoicePayload) {
  const connection = getConnection();
  const currencyMint = new PublicKey(getRequiredEnv("CURRENCY_MINT"));
  const userPublicKey = new PublicKey(invoice.wallet);
  const agent = getAgent(connection);
  const invoiceId = deriveInvoiceId(invoice);

  const existingInvoice = await connection.getAccountInfo(invoiceId, "confirmed");
  if (existingInvoice) {
    throw new Error("Generated invoice already exists. Please request a new invoice.");
  }

  const instructions = await agent.buildAcceptPaymentInstructions({
    user: userPublicKey,
    currencyMint,
    amount: invoice.amount,
    memo: invoice.memo,
    startTime: invoice.startTime,
    endTime: invoice.endTime,
  });

  const { blockhash } = await connection.getLatestBlockhash("confirmed");
  const transaction = new Transaction();
  transaction.recentBlockhash = blockhash;
  transaction.feePayer = userPublicKey;
  transaction.add(...instructions);

  return {
    invoiceId: invoiceId.toBase58(),
    transaction: transaction
      .serialize({ requireAllSignatures: false })
      .toString("base64"),
  };
}

export async function issuePaymentInvoice(wallet: string) {
  pruneIssuedInvoices();

  const invoice = createInvoiceParams(wallet);
  const payment = await buildPaymentTransaction(invoice);
  const invoiceToken = signTokenPayload({
    kind: "invoice",
    version: TOKEN_VERSION,
    invoiceId: payment.invoiceId,
    ...invoice,
  });
  const issuedInvoice: IssuedInvoice = {
    ...invoice,
    ...payment,
    invoiceToken,
    createdAt: Date.now(),
  };

  getIssuedInvoices().set(payment.invoiceId, issuedInvoice);
  return issuedInvoice;
}

export function getIssuedInvoice(invoiceId: string, invoiceToken: string | undefined) {
  pruneIssuedInvoices();

  if (!invoiceToken) return null;

  const invoice = getIssuedInvoices().get(invoiceId);
  if (invoice && invoice.invoiceToken === invoiceToken) return invoice;

  const payload = verifyTokenPayload<InvoiceTokenPayload>(invoiceToken);
  if (!payload || payload.kind !== "invoice" || payload.version !== TOKEN_VERSION) return null;
  if (payload.invoiceId !== invoiceId) return null;

  const invoicePayload: InvoicePayload = {
    wallet: payload.wallet,
    amount: payload.amount,
    memo: payload.memo,
    startTime: payload.startTime,
    endTime: payload.endTime,
  };
  assertInvoicePayload(invoicePayload);

  if (invoicePayload.endTime < Math.floor(Date.now() / 1000)) return null;
  if (deriveInvoiceId(invoicePayload).toBase58() !== invoiceId) return null;

  return {
    ...invoicePayload,
    invoiceId,
    invoiceToken,
    transaction: "",
    createdAt: 0,
  } satisfies IssuedInvoice;
}

export function markInvoiceVerified(invoiceId: string) {
  const invoice = getIssuedInvoices().get(invoiceId);
  if (invoice) {
    invoice.verifiedAt = Date.now();
  }
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function verifyInvoicePayment(invoice: InvoicePayload) {
  const agent = getAgent();
  const params = {
    user: new PublicKey(invoice.wallet),
    currencyMint: new PublicKey(getRequiredEnv("CURRENCY_MINT")),
    amount: invoice.amount,
    memo: invoice.memo,
    startTime: invoice.startTime,
    endTime: invoice.endTime,
  };

  for (let attempt = 1; attempt <= PAYMENT_VERIFY_RETRY_ATTEMPTS; attempt += 1) {
    if (await agent.validateInvoicePayment(params)) {
      return true;
    }

    if (attempt < PAYMENT_VERIFY_RETRY_ATTEMPTS) {
      await delay(PAYMENT_VERIFY_RETRY_DELAY_MS);
    }
  }

  return false;
}

export function grantAccess(wallet: string) {
  const expiresAt = Date.now() + ACCESS_TTL_MS;
  const accessToken = signTokenPayload({
    kind: "access",
    version: TOKEN_VERSION,
    wallet,
    expiresAt,
  });

  return { accessToken, expiresAt };
}

export function hasAccess(accessToken: string | undefined) {
  if (!accessToken) return false;

  const payload = verifyTokenPayload<AccessTokenPayload>(accessToken);
  if (!payload || payload.kind !== "access" || payload.version !== TOKEN_VERSION) {
    return false;
  }

  return payload.expiresAt > Date.now();
}
