"""Compare installed Ollama text models using only a loopback HTTP connection."""

import argparse
import http.client
import json
import time
from datetime import datetime, timezone
from pathlib import Path


CASES = {
    "gta_bike": ("GTA", "I missed the ramp. The bike fell into the canal. I'm swimming back to shore."),
    "roblox_obby": ("Roblox", "Wait for the blue platform. Now jump! I made the checkpoint with one second left."),
    "unresolved": ("Racing game", "Final turn. We're side by side. The recording cuts off before the finish."),
    "correction": ("Roblox", "I thought the vault was open. Nope, still locked. We went back for the key."),
}
PROMPT = ("Write one short English title for this gameplay clip. Use at most 60 characters. "
          "Return only the title as a single plain-text line. Ground every claim in the "
          "transcript. Do not invent an outcome, add hashtags, or quote the title.\n"
          "Game: {game}\nTranscript: {transcript}")
OPTIONS = {"temperature": 0, "seed": 42, "num_predict": 48, "num_ctx": 1024}


def request(port, endpoint, payload=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=240)
    try:
        body = json.dumps(payload) if payload is not None else None
        connection.request("POST" if body else "GET", "/api/" + endpoint, body,
                           {"Content-Type": "application/json"})
        response = connection.getresponse()
        data = json.loads(response.read())
        if response.status != 200:
            raise RuntimeError(f"Ollama {response.status}: {data}")
        return data
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    installed = {model["name"]: model for model in request(args.port, "tags")["models"]}
    models = ("qwen2.5:7b", "gemma2:9b")
    missing = set(models).difference(installed)
    if missing:
        raise SystemExit("Install these models separately: " + ", ".join(sorted(missing)))
    report = {"started_utc": datetime.now(timezone.utc).isoformat(),
              "ollama": request(args.port, "version")["version"], "options": OPTIONS,
              "prompt_template": PROMPT, "cases": CASES,
              "models": {name: {k: installed[name][k] for k in ("digest", "details", "size")}
                         for name in models}, "runs": []}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as output:
        for name in models:
            for case_id, (game, transcript) in CASES.items():
                start = time.perf_counter()
                data = request(args.port, "generate", {
                    "model": name, "prompt": PROMPT.format(game=game, transcript=transcript),
                    "stream": False, "keep_alive": "1m", "options": OPTIONS})
                title = data["response"].strip()
                report["runs"].append({"case": case_id, "model": name, "title": title,
                    "single_line": bool(title) and len(title.splitlines()) == 1,
                    "char_count": len(title), "no_hashtag": "#" not in title,
                    "no_wrapping_quotes": not title.startswith(('"', "'", "“", "‘")),
                    "wall_seconds": round(time.perf_counter() - start, 3),
                    "load_seconds": round(data["load_duration"] / 1e9, 3),
                    "output_tokens": data.get("eval_count"), "done_reason": data.get("done_reason")})
                output.seek(0)
                json.dump(report, output, indent=2)
                output.truncate()
                output.flush()
                print(f"{name} {case_id} finished", flush=True)
            request(args.port, "generate", {"model": name, "keep_alive": 0, "stream": False})


if __name__ == "__main__":
    main()
