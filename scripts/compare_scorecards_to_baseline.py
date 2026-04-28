import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def extract_scorecard_id(scorecard_url: str) -> str:
    parsed = urlparse(scorecard_url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[-2] == "scorecards":
        return parts[-1]
    if parts and len(parts[-1]) >= 8:
        return parts[-1]
    raise ValueError(f"Could not extract scorecard id from URL: {scorecard_url}")


def load_local_scorecard_state(repo: Path) -> dict:
    graph = json.loads((repo / "reports" / "scorecard_graph.json").read_text())
    closure = json.loads((repo / "reports" / "scorecard_closure_result.json").read_text())

    nodes = graph.get("nodes", [])
    final_score = graph.get("final_score", {})
    closures = closure.get("closures", [])
    closure_by_id = {c.get("card_id"): c for c in closures}

    card_summaries = []
    for node in nodes:
        card_id = node.get("card_id")
        c = closure_by_id.get(card_id, {})
        card_summaries.append(
            {
                "card_id": card_id,
                "stage": node.get("stage"),
                "opened_timestamp_utc": node.get("timestamp_utc"),
                "closed": bool(c.get("closed", False)),
                "guid_count": int(c.get("guid_count", 0)),
                "game_guid_count": int(c.get("game_guid_count", 0)),
                "best_clicks": node.get("best_clicks"),
                "solved_rate": node.get("solved_rate"),
            }
        )

    return {
        "count": len(card_summaries),
        "opened_and_closed": sum(1 for item in card_summaries if item["closed"]),
        "cards": card_summaries,
        "final_scorecard": {
            "card_id": final_score.get("card_id"),
            "best_clicks": final_score.get("best_clicks"),
            "solved_rate": final_score.get("solved_rate"),
        },
    }


def load_baseline_rows_from_file(path: str) -> list[dict]:
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, dict):
        payload = payload.get("rows", [])
    if not isinstance(payload, list):
        raise ValueError("Baseline rows file must be a JSON list or an object with a 'rows' list")
    return payload


def try_fetch_scorecard_html(url: str) -> tuple[list[dict], str]:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", "ignore")
    except HTTPError as e:
        return [], f"http_error_{e.code}"
    except URLError:
        return [], "network_blocked"

    # Best-effort parsing for rows shown as table-like lines in page text.
    rows = []
    pattern = re.compile(r"\b([1-7])\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+)\s+([0-9]+)\b")
    for match in pattern.finditer(html):
        idx, score, won, actions = match.groups()
        row = {
            "game_index": int(idx),
            "score": float(score),
            "won": int(won),
            "actions": int(actions),
        }
        if row not in rows:
            rows.append(row)
    rows.sort(key=lambda r: r["game_index"])
    if len(rows) >= 7:
        return rows[:7], "fetched_from_url"
    return [], "fetched_but_rows_not_found"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline_scorecard_url")
    parser.add_argument("--baseline-rows-file", default=None)
    parser.add_argument("--baseline-solved-rate", type=float, default=None)
    parser.add_argument("--baseline-best-clicks", type=int, default=None)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    baseline_id = extract_scorecard_id(args.baseline_scorecard_url)
    local_state = load_local_scorecard_state(repo)

    retrieval_status = "unavailable"
    baseline_rows: list[dict] = []
    warnings = []

    if args.baseline_rows_file:
        baseline_rows = load_baseline_rows_from_file(args.baseline_rows_file)
        retrieval_status = "loaded_from_file"
    else:
        baseline_rows, retrieval_status = try_fetch_scorecard_html(args.baseline_scorecard_url)
        if not baseline_rows:
            warnings.append(
                "Could not fetch/parse official baseline rows from URL; use --baseline-rows-file to provide them explicitly."
            )

    final_scorecard = local_state["final_scorecard"]
    metric_deltas = {"best_clicks_delta_vs_baseline": None, "solved_rate_delta_vs_baseline": None}

    if args.baseline_best_clicks is not None and final_scorecard.get("best_clicks") is not None:
        metric_deltas["best_clicks_delta_vs_baseline"] = final_scorecard["best_clicks"] - args.baseline_best_clicks
    else:
        warnings.append("Baseline best-clicks missing; unable to compute best-clicks delta.")

    if args.baseline_solved_rate is not None and final_scorecard.get("solved_rate") is not None:
        metric_deltas["solved_rate_delta_vs_baseline"] = round(final_scorecard["solved_rate"] - args.baseline_solved_rate, 6)
    else:
        warnings.append("Baseline solved-rate missing; unable to compute solved-rate delta.")

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "official_baseline": {
            "url": args.baseline_scorecard_url,
            "scorecard_id": baseline_id,
            "retrieval_status": retrieval_status,
            "best_clicks": args.baseline_best_clicks,
            "solved_rate": args.baseline_solved_rate,
            "rows": baseline_rows,
        },
        "local_scorecards": local_state,
        "comparison": {"metric_deltas": metric_deltas, "warnings": warnings},
    }

    out = repo / "reports" / "scorecard_baseline_comparison.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
