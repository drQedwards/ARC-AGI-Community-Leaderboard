#!/usr/bin/env python3
"""Inspect the current on-chain state for a Solana address from a backend terminal.

The script intentionally uses raw JSON-RPC over the standard library so it can run
inside minimal cloud shells without the Solana CLI. It writes a structured report
whether the live fetch succeeds or the cloud/RPC boundary blocks the request.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ADDRESS = "B4cd9KaWdk6vqCxE9WRv3WVmZv26joZfQyG7q57xpump"
DEFAULT_RPC_URL = "https://rpc.solanatracker.io/public"


def rpc_request(rpc_url: str, method: str, params: list[Any]) -> Any:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(
        "utf-8"
    )
    request = urllib.request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return data["result"]


def summarize_account(account_info: dict[str, Any] | None) -> dict[str, Any]:
    if account_info is None:
        return {"exists": False}

    data = account_info.get("data")
    parsed = data.get("parsed") if isinstance(data, dict) else None
    parsed_info = parsed.get("info") if isinstance(parsed, dict) else None

    return {
        "exists": True,
        "lamports": account_info.get("lamports"),
        "owner": account_info.get("owner"),
        "executable": account_info.get("executable"),
        "rent_epoch": account_info.get("rentEpoch"),
        "parsed_type": parsed.get("type") if isinstance(parsed, dict) else None,
        "mint_authority": parsed_info.get("mintAuthority") if isinstance(parsed_info, dict) else None,
        "supply": parsed_info.get("supply") if isinstance(parsed_info, dict) else None,
        "decimals": parsed_info.get("decimals") if isinstance(parsed_info, dict) else None,
        "freeze_authority": parsed_info.get("freezeAuthority") if isinstance(parsed_info, dict) else None,
    }


def inspect_address(address: str, rpc_url: str, signature_limit: int) -> dict[str, Any]:
    account = rpc_request(rpc_url, "getAccountInfo", [address, {"encoding": "jsonParsed"}])
    signatures = rpc_request(rpc_url, "getSignaturesForAddress", [address, {"limit": signature_limit}])

    supply = None
    largest_accounts = None
    if account.get("value") is not None:
        try:
            supply = rpc_request(rpc_url, "getTokenSupply", [address])
        except Exception as exc:
            supply = {"status": "unavailable", "error": str(exc)}
        try:
            largest_accounts = rpc_request(rpc_url, "getTokenLargestAccounts", [address])
        except Exception as exc:
            largest_accounts = {"status": "unavailable", "error": str(exc)}

    return {
        "status": "ok",
        "address": address,
        "rpc_url": rpc_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "account": summarize_account(account.get("value")),
        "token_supply": supply,
        "token_largest_accounts": largest_accounts,
        "recent_signatures": signatures,
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect current Solana account/token state over JSON-RPC.")
    parser.add_argument("--address", default=os.getenv("AGENT_TOKEN_MINT_ADDRESS") or DEFAULT_ADDRESS)
    parser.add_argument("--rpc-url", default=os.getenv("SOLANA_RPC_URL") or DEFAULT_RPC_URL)
    parser.add_argument("--signature-limit", type=int, default=10)
    parser.add_argument("--output", default="reports/solana_address_state.json")
    return parser.parse_args()


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    args = parse_args()
    output = repo / args.output

    try:
        report = inspect_address(args.address, args.rpc_url, args.signature_limit)
    except Exception as exc:
        report = {
            "status": "fetch_failed",
            "address": args.address,
            "rpc_url": args.rpc_url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
            "note": "The backend terminal could not reach the configured Solana RPC; rerun from a cloud environment with RPC egress enabled or pass --rpc-url.",
        }

    write_report(output, report)
    print(json.dumps({**report, "output": str(output.relative_to(repo))}, indent=2))
    if report["status"] != "ok":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
