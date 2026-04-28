import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run_cmd(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def write_and_print_result(repo: Path, result: dict):
    out_json = repo / "reports" / "supermodel_memory_graph_result.json"
    out_json.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def main():
    repo = Path(__file__).resolve().parent.parent
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "local_cli": {},
        "api_cli": {},
        "status": "unknown",
    }

    supermodel_api_key = os.getenv("SUPERMODEL_API_KEY")
    if not supermodel_api_key:
        result["status"] = "missing_env_var"
        result["message"] = "Missing required environment variable: SUPERMODEL_API_KEY"
        write_and_print_result(repo, result)
        return

    # Full local memory graph string (disc/context string)
    rc, out, err = run_cmd(["uncompact", "dry-run", "--mode", "local", "--max-tokens", "12000"], repo)
    (repo / "reports" / "supermodel_memory_graph_full.txt").write_text(out)
    result["local_cli"] = {
        "return_code": rc,
        "stderr": err.strip(),
        "output_file": "reports/supermodel_memory_graph_full.txt",
        "output_chars": len(out),
    }

    # Attempt API path as requested (may fail due environment network policy)
    env = os.environ.copy()
    env["SUPERMODEL_API_KEY"] = supermodel_api_key
    p = subprocess.run(
        ["uncompact", "dry-run", "--mode", "api", "--max-tokens", "12000"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )
    (repo / "reports" / "supermodel_memory_graph_api_attempt.txt").write_text(p.stdout)
    result["api_cli"] = {
        "return_code": p.returncode,
        "stderr": p.stderr.strip(),
        "output_file": "reports/supermodel_memory_graph_api_attempt.txt",
        "output_chars": len(p.stdout),
    }
    result["status"] = "completed" if p.returncode == 0 else "api_cli_failed"

    write_and_print_result(repo, result)


if __name__ == "__main__":
    main()
