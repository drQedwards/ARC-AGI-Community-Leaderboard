#!/usr/bin/env python3
"""Fetch, validate, rewind, and copy a scorecard graph.

The default source is reports/scorecard_graph.json. The script also accepts an
HTTP(S) URL for cases where a graph artifact needs to be fetched from CI or a
remote report store.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def fetch_graph(source: str, repo: Path) -> dict[str, Any]:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = repo / source_path
    return json.loads(source_path.read_text())


def validate_graph(graph: dict[str, Any]) -> None:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("Graph must contain a non-empty nodes list.")
    if not isinstance(edges, list):
        raise ValueError("Graph must contain an edges list.")

    node_ids = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError(f"Node at index {index} must be an object.")
        card_id = node.get("card_id")
        if not isinstance(card_id, str) or not card_id:
            raise ValueError(f"Node at index {index} is missing a card_id string.")
        if card_id in node_ids:
            raise ValueError(f"Duplicate node card_id: {card_id}")
        node_ids.add(card_id)

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError(f"Edge at index {index} must be an object.")
        source = edge.get("from")
        target = edge.get("to")
        if source not in node_ids or target not in node_ids:
            raise ValueError(
                f"Edge at index {index} references unknown nodes: {source!r} -> {target!r}"
            )


def rewind_graph(graph: dict[str, Any], source: str) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    rewound_edges = []
    for edge in reversed(graph["edges"]):
        rewound_edge = dict(edge)
        original_from = edge["from"]
        original_to = edge["to"]
        rewound_edge["from"] = original_to
        rewound_edge["to"] = original_from
        rewound_edge["rewound_from"] = {
            "from": original_from,
            "to": original_to,
        }
        rewound_edges.append(rewound_edge)

    return {
        **graph,
        "generated_at": generated_at,
        "rewound_at": generated_at,
        "rewound_source": source,
        "nodes": list(reversed(graph["nodes"])),
        "edges": rewound_edges,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch, validate, rewind, and copy a scorecard graph artifact."
    )
    parser.add_argument("--source", default="reports/scorecard_graph.json")
    parser.add_argument("--rewound-output", default="reports/scorecard_graph_rewound.json")
    parser.add_argument("--copy-output", default="reports/scorecard_graph_copy.json")
    return parser.parse_args()


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    args = parse_args()

    graph = fetch_graph(args.source, repo)
    validate_graph(graph)

    copy_graph = {
        **graph,
        "copied_at": datetime.now(timezone.utc).isoformat(),
        "copied_source": args.source,
    }
    rewound_graph = rewind_graph(graph, args.source)
    validate_graph(rewound_graph)

    copy_output = repo / args.copy_output
    rewound_output = repo / args.rewound_output
    write_json(copy_output, copy_graph)
    write_json(rewound_output, rewound_graph)

    result = {
        "source": args.source,
        "copy_output": str(copy_output.relative_to(repo)),
        "rewound_output": str(rewound_output.relative_to(repo)),
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "status": "ok",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
