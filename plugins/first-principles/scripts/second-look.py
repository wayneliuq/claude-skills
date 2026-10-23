#!/usr/bin/env python3
"""Run every enabled second-look lane on one brief, in parallel.

usage: second-look.py BRIEF_FILE WORKDIR OUT_DIR [LANE ...]

Each lane's output goes to OUT_DIR/<lane>.md as it streams. Prints one status line per lane.
"""
import json
import os
import shutil
import subprocess
import sys
import time

USER_CONFIG = os.path.expanduser("~/.claude/first-principles/second-looks.json")
DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "second-looks.json")


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    brief_file, workdir, out_dir, only = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    config_path = os.environ.get("SECOND_LOOKS_CONFIG") or (USER_CONFIG if os.path.exists(USER_CONFIG) else DEFAULT_CONFIG)
    config = json.load(open(config_path))
    workdir = os.path.abspath(workdir)
    # Some harnesses run from their own folder whatever the launch folder is, so the brief names it.
    prompt = f"Work only in the repository at {workdir} (cd there first).\n\n" + open(brief_file).read()
    os.makedirs(out_dir, exist_ok=True)

    running = []
    for lane in config["lanes"]:
        name = lane["name"]
        if only and name not in only:
            continue
        if not lane.get("enabled", True):
            print(f"{name}: skipped (disabled)")
            continue
        if shutil.which(lane["command"][0]) is None:
            print(f"{name}: skipped ({lane['command'][0]} not installed)")
            continue
        argv = [prompt if a == "{prompt}" else a for a in lane["command"]]
        out = open(os.path.join(out_dir, f"{name}.md"), "w")
        proc = subprocess.Popen(argv, cwd=workdir, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        running.append((name, proc, out, time.time(), lane.get("fail_patterns", [])))

    deadline = time.time() + config.get("timeout_seconds", 900)
    ended = {}
    while len(ended) < len(running) and time.time() < deadline:
        for name, proc, *_ in running:
            if name not in ended and proc.poll() is not None:
                ended[name] = time.time()
        time.sleep(0.5)
    for name, proc, out, start, fail_patterns in running:
        if name in ended:
            status = "ok" if proc.returncode == 0 else f"failed (exit {proc.returncode})"
        else:
            proc.kill()
            proc.wait()
            ended[name] = time.time()
            status = "timed out"
        out.close()
        size = os.path.getsize(out.name)
        text = open(out.name, errors="replace").read()
        hit = next((p for p in fail_patterns if p in text), None)
        if hit:
            status = f"refused: {hit}"
        elif status == "ok" and size == 0:
            status = "no output (quota or transport?)"
        print(f"{name}: {status} in {int(ended[name] - start)}s -> {out.name} ({size} bytes)")
    print(f"config: {config_path}")


if __name__ == "__main__":
    main()
