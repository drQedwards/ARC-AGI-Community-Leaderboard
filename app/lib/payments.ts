import { randomBytes, randomUUID } from "crypto";
import {
  getInvoiceIdPDA,
  PumpAgent,
} from "@pump-fun/agent-payments-sdk";
import { Connection, PublicKey, Transaction } from "@solana/web3.js";

export const SOL_DECIMALS = 9;
export const DEFAULT_INVOICE_TTL_SECONDS = 15 * 60;
export const ACCESS_TTL_MS = 60 * 60 * 1000;

type AccessGrant = {
  wallet: string;
  expiresAt: number;
};

type GlobalAccessState = typeof globalThis & {
  __rngAccessGrants?: Map<string, AccessGrant>;
};

export type InvoicePayload = {
  wallet: string;
  amount: number;
  memo: number;
  startTime: number;
  endTime: number;
};

export function getAccessGrants() {
  const state = globalThis as GlobalAccessState;
  state.__rngAccessGrants ??= new Map<string, AccessGrant>();
  return state.__rngAccessGrants;
}

function getRequiredEnv(name: string) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
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

  if (endTime <= startTime) {
    throw new Error("Invoice endTime must be greater than startTime.");
  }

  return {
    wallet,
    amount: getPriceAmount(),
    memo,
    startTime,
    endTime,
  };
}

export async function buildPaymentTransaction(invoice: InvoicePayload) {
  const connection = getConnection();
  const agentMint = new PublicKey(getRequiredEnv("AGENT_TOKEN_MINT_ADDRESS"));
  const currencyMint = new PublicKey(getRequiredEnv("CURRENCY_MINT"));
  const userPublicKey = new PublicKey(invoice.wallet);
  const agent = getAgent(connection);

  const [invoiceId] = getInvoiceIdPDA(
    agentMint,
    currencyMint,
    invoice.amount,
    invoice.memo,
    invoice.startTime,
    invoice.endTime,
  );

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

export async function verifyInvoicePayment(invoice: InvoicePayload) {
  const agent = getAgent();
  return agent.validateInvoicePayment({
    user: new PublicKey(invoice.wallet),
    currencyMint: new PublicKey(getRequiredEnv("CURRENCY_MINT")),
    amount: invoice.amount,
    memo: invoice.memo,
    startTime: invoice.startTime,
    endTime: invoice.endTime,
  });
}

export function grantAccess(wallet: string) {
  const accessToken = randomUUID();
  const expiresAt = Date.now() + ACCESS_TTL_MS;
  getAccessGrants().set(accessToken, { wallet, expiresAt });
  return { accessToken, expiresAt };
}

export function hasAccess(accessToken: string | undefined) {
  if (!accessToken) return false;
  const grants = getAccessGrants();
  const grant = grants.get(accessToken);
  if (!grant) return false;
  if (grant.expiresAt <= Date.now()) {
    grants.delete(accessToken);
    return false;
  }
  return true;
}
