import json
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dependency_error_result(message: str):
    return {
        "timestamp_utc": _utc_now(),
        "mode": "competition",
        "status": "dependency_missing",
        "error": message,
        "scorecard_opened": False,
        "scorecard": None,
        "scorecard_closeout": {
            "attempted": False,
            "status": "skipped_dependency_missing",
            "events": [],
        },
    }


def _close_scorecard_offline(arc_agi_mod, operation_mode, api_key: str, scorecard_obj):
    closeout = {
        "attempted": True,
        "mode": "offline",
        "timestamp_utc": _utc_now(),
        "status": "not_started",
        "events": [],
    }

    card_id = None
    if hasattr(scorecard_obj, "model_dump"):
        payload = scorecard_obj.model_dump()
        card_id = payload.get("id") or payload.get("card_id")
    elif isinstance(scorecard_obj, dict):
        card_id = scorecard_obj.get("id") or scorecard_obj.get("card_id")

    if not card_id:
        closeout["status"] = "skipped_missing_card_id"
        return closeout

    closeout["card_id"] = card_id

    try:
        arc_offline = arc_agi_mod.Arcade(
            operation_mode=operation_mode.OFFLINE,
            arc_api_key=api_key,
        )
        sm = arc_offline.scorecard_manager
        closed, guids, gid_guids = sm.close_scorecard(card_id, api_key)
        closeout["status"] = "closed" if closed is not None else "close_returned_none"
        closeout["events"].append(
            {
                "event": "close_scorecard",
                "closed": closed is not None,
                "guid_count": len(guids or []),
                "game_guid_count": len(gid_guids or []),
            }
        )
    except Exception as e:
        closeout["status"] = "close_failed"
        closeout["error"] = str(e)

    return closeout


def main():
    repo = Path(__file__).resolve().parent.parent
    arc_api_key = "940cff7a-fce5-436c-a164-2ca9a7ea32c5"

    try:
        import arc_agi
        from arc_agi.base import OperationMode
        from arcengine import GameAction
    except Exception as e:
        result = _dependency_error_result(str(e))
        out = repo / "reports" / "arcagi3_competition_mode_result.json"
        out.write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return

    result = {
        "timestamp_utc": _utc_now(),
        "mode": "competition",
        "arc_api_key_used": arc_api_key,
        "available_environments": 0,
        "games_attempted": [],
        "scorecard_opened": False,
        "scorecard": None,
        "status": "unknown",
        "scorecard_closeout": {
            "attempted": False,
            "status": "skipped_not_completed",
            "events": [],
        },
    }

    try:
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

        if result["status"] == "completed" and result["scorecard"]:
            sc_obj = sc if "sc" in locals() else result["scorecard"]
            result["scorecard_closeout"] = _close_scorecard_offline(
                arc_agi,
                OperationMode,
                arc_api_key,
                sc_obj,
            )

    except Exception as e:
        result["status"] = "failed_initialization"
        result["init_error"] = str(e)

    out = repo / "reports" / "arcagi3_competition_mode_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
