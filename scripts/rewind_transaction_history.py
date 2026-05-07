#!/usr/bin/env python3
"""Fetch, validate, copy, and rewind Solana transaction history.

By default the script uses a local fixture so it can run in CI without a Solana
RPC key. Pass --address to fetch live signatures for a wallet, mint, or PDA via
getSignaturesForAddress.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_RPC_URL = "https://rpc.solanatracker.io/public"


def read_json_source(source: str, repo: Path) -> Any:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = repo / source_path
    return json.loads(source_path.read_text())


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


def fetch_transaction_history(args: argparse.Namespace, repo: Path) -> tuple[list[dict[str, Any]], str]:
    if args.address:
        rpc_url = args.rpc_url or os.getenv("SOLANA_RPC_URL") or DEFAULT_RPC_URL
        result = rpc_request(rpc_url, "getSignaturesForAddress", [args.address, {"limit": args.limit}])
        return result, f"rpc:{args.address}"

    data = read_json_source(args.source, repo)
    if isinstance(data, list):
        return data, args.source
    if isinstance(data, dict) and isinstance(data.get("transactions"), list):
        return data["transactions"], args.source
    if isinstance(data, dict) and isinstance(data.get("signatures"), list):
        return data["signatures"], args.source
    raise ValueError("Transaction history source must be a list or contain transactions/signatures.")


def validate_transaction_history(history: list[dict[str, Any]]) -> None:
    seen_signatures = set()
    for index, item in enumerate(history):
        if not isinstance(item, dict):
            raise ValueError(f"Transaction at index {index} must be an object.")

        signature = item.get("signature")
        if not isinstance(signature, str) or not signature:
            raise ValueError(f"Transaction at index {index} is missing a signature string.")
        if signature in seen_signatures:
            raise ValueError(f"Duplicate transaction signature: {signature}")
        seen_signatures.add(signature)

        slot = item.get("slot")
        if slot is not None and (not isinstance(slot, int) or slot < 0):
            raise ValueError(f"Transaction {signature} has an invalid slot.")

        block_time = item.get("blockTime")
        if block_time is not None and (not isinstance(block_time, int) or block_time < 0):
            raise ValueError(f"Transaction {signature} has an invalid blockTime.")


def copy_history(history: list[dict[str, Any]], source: str) -> dict[str, Any]:
    copied_at = datetime.now(timezone.utc).isoformat()
    return {
        "copied_at": copied_at,
        "copied_source": source,
        "order": "rpc-newest-first",
        "transactions": history,
    }


def rewind_history(history: list[dict[str, Any]], source: str) -> dict[str, Any]:
    rewound_at = datetime.now(timezone.utc).isoformat()
    rewound = []
    last_index = len(history) - 1
    for rewound_index, transaction in enumerate(reversed(history)):
        rewound_item = dict(transaction)
        rewound_item["rewound_index"] = rewound_index
        rewound_item["original_index"] = last_index - rewound_index
        rewound.append(rewound_item)

    return {
        "rewound_at": rewound_at,
        "rewound_source": source,
        "order": "oldest-first",
        "transactions": rewound,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def display_path(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch/copy Solana transaction history and emit an oldest-first rewound copy."
    )
    parser.add_argument("--source", default="data/transaction_history_example.json")
    parser.add_argument("--address", help="Solana address to fetch with getSignaturesForAddress")
    parser.add_argument("--rpc-url", help="Solana RPC URL; defaults to SOLANA_RPC_URL or public RPC")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--copy-output", default="reports/transaction_history_copy.json")
    parser.add_argument("--rewound-output", default="reports/transaction_history_rewound.json")
    return parser.parse_args()


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    args = parse_args()

    try:
        history, source_label = fetch_transaction_history(args, repo)
        validate_transaction_history(history)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "source": f"rpc:{args.address}" if args.address else args.source,
                    "status": "fetch_failed",
                    "error": str(exc),
                },
                indent=2,
            )
        )
        raise SystemExit(2) from exc

    copied = copy_history(history, source_label)
    rewound = rewind_history(history, source_label)
    validate_transaction_history(copied["transactions"])
    validate_transaction_history(rewound["transactions"])

    copy_output = repo / args.copy_output
    rewound_output = repo / args.rewound_output
    write_json(copy_output, copied)
    write_json(rewound_output, rewound)

    print(
        json.dumps(
            {
                "source": source_label,
                "copy_output": display_path(copy_output, repo),
                "rewound_output": display_path(rewound_output, repo),
                "transactions": len(history),
                "status": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
