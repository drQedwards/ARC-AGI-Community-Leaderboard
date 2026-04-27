import json
from datetime import datetime, timezone
from pathlib import Path

import arc_agi
from arc_agi.base import OperationMode
from arcengine import GameAction


def main():
    repo = Path(__file__).resolve().parent.parent
    arc_api_key = "940cff7a-fce5-436c-a164-2ca9a7ea32c5"

    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "competition",
        "arc_api_key_used": arc_api_key,
        "available_environments": 0,
        "games_attempted": [],
        "scorecard_opened": False,
        "scorecard": None,
        "status": "unknown",
    }

    try:
        arc = arc_agi.Arcade(operation_mode=OperationMode.COMPETITION, arc_api_key=arc_api_key)
        result["available_environments"] = len(arc.available_environments)

        target_games = [e.game_id for e in arc.available_environments[:10]] or ["ls20", "ft09"]

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

    out = repo / "reports" / "arcagi3_competition_mode_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
