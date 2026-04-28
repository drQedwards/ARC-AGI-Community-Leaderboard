import json
import os
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_ENV_VAR = "ARC_API_KEY"


def write_and_print_result(repo: Path, result: dict):
    out = repo / "reports" / "arcagi3_competition_mode_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def main():
    repo = Path(__file__).resolve().parent.parent
    arc_api_key = os.getenv(REQUIRED_ENV_VAR)

    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "competition",
        "available_environments": 0,
        "games_attempted": [],
        "scorecard_opened": False,
        "scorecard": None,
        "status": "unknown",
    }

    if not arc_api_key:
        result["status"] = "missing_env_var"
        result["message"] = f"Missing required environment variable: {REQUIRED_ENV_VAR}"
        write_and_print_result(repo, result)
        return

    try:
        import arc_agi
        from arc_agi.base import OperationMode
        from arcengine import GameAction

        arc = arc_agi.Arcade(operation_mode=OperationMode.COMPETITION, arc_api_key=arc_api_key)
        result["available_environments"] = len(arc.available_environments)

        default_7_games = ["ls20", "ft09", "bb24", "ag06", "hz17", "dd33", "rm15"]
        target_games = [e.game_id for e in arc.available_environments[:7]] or default_7_games

        for game_id in target_games:
            item = {"game_id": game_id, "status": "not_started", "error": None}
            try:
                env = arc.make(game_id)
                if env is None:
                    item["status"] = "make_returned_none"
                else:
                    for _ in range(5):
                        env.step(GameAction.ACTION1)
                    item["status"] = "played_5_actions"
            except Exception as e:
                item["status"] = "failed"
                item["error"] = str(e)
            result["games_attempted"].append(item)

        solved = sum(1 for g in result["games_attempted"] if g["status"] == "played_5_actions")
        failed = sum(1 for g in result["games_attempted"] if g["status"] == "failed")
        result["final_score_7_games"] = {
            "games_attempted": len(result["games_attempted"]),
            "games_played_successfully": solved,
            "games_failed": failed,
            "success_rate": round(solved / len(result["games_attempted"]), 3)
            if result["games_attempted"]
            else 0.0,
        }

        try:
            sc = arc.get_scorecard()
            result["scorecard_opened"] = True
            result["scorecard"] = sc.model_dump() if hasattr(sc, "model_dump") else str(sc)
            result["status"] = "completed"
        except Exception as e:
            result["scorecard_opened"] = False
            result["status"] = "blocked_opening_scorecard"
            result["scorecard_error"] = str(e)

    except Exception as e:
        result["status"] = "failed_initialization"
        result["init_error"] = str(e)

    write_and_print_result(repo, result)


if __name__ == "__main__":
    main()
