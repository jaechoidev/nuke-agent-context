#!/usr/bin/env python3
"""Two-arm ablation: does the nuke-context plugin beat vanilla Claude Code?

  with     - a bare directory + the shipped plugin via --plugin-dir
  without  - a bare directory, no plugin

The with-arm is exactly the installed experience: the plugin needs no setup,
so the ONLY difference between arms is the plugin itself. Each run also
records its cost and token usage, so the context-overhead question is
answered with a measured column next to the compile rate.

Grading is objective throughout: the headers say whether a symbol exists and
the compiler says whether the code works. No LLM judge.

Usage:
  python3 evals/run_ablation.py --runs 1 --model sonnet
  python3 evals/run_ablation.py --case 01 --arm with --verbose
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import statistics
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins" / "nuke-context"
CASES = REPO / "evals" / "cases"

sys.path.insert(0, str(REPO / "evals" / "graders"))
import grade as G  # noqa: E402

PREAMBLE = (
    "Write the code as a single fenced ```cpp block. "
    "Do not create files; print the code in your reply."
)


def run_arm(prompt: str, cwd: pathlib.Path, with_plugin: bool,
            model: str, timeout: int) -> dict:
    # Both arms run with identical permissions -- the ONLY difference between
    # them is the plugin. Headless -p mode denies reads outside the cwd by
    # default, and the Nuke headers live in /Applications, so without this the
    # with-arm's whole mechanism (read the real header) is silently disabled
    # and the comparison is meaningless. Safe here: every run is a throwaway
    # temp dir and the grader never executes the generated code.
    cmd = ["claude", "-p", prompt, "--model", model,
           "--permission-mode", "bypassPermissions",
           "--output-format", "json"]
    if with_plugin:
        cmd += ["--plugin-dir", str(PLUGIN)]
    empty = {"text": "", "cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0}
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return empty
    try:
        payload = json.loads(r.stdout)
    except (json.JSONDecodeError, ValueError):
        # Not JSON (CLI error path): grade whatever text came out, cost unknown.
        return dict(empty, text=r.stdout)
    usage = payload.get("usage") or {}
    return {"text": payload.get("result", ""),
            "cost_usd": payload.get("total_cost_usd", 0.0),
            "input_tokens": usage.get("input_tokens", 0)
                            + usage.get("cache_read_input_tokens", 0)
                            + usage.get("cache_creation_input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0)}


def summarise(results: list[dict]) -> dict:
    """Aggregate per-arm. Hallucination counts are what this toolkit targets."""
    if not results:
        return {}
    n = len(results)
    compiled = sum(1 for r in results if r["build"].get("compiles") is True)
    bad_inc = sum(len(r["includes"]["invalid"]) for r in results)
    bad_sym = sum(len(r["symbols"]["invalid"]) for r in results)
    tot_inc = sum(r["includes"]["total"] for r in results)
    tot_sym = sum(r["symbols"]["total"] for r in results)
    no_code = sum(1 for r in results if not r["produced_code"])

    # The compiler is the authoritative hallucination oracle: it names the
    # invented member or type outright. Source regexes miss the dominant case,
    # a plausible method on a real class, and miss it entirely when the code
    # writes `using namespace DD::Image` and never qualifies anything.
    invented = []
    for r in results:
        invented += r["build"].get("invented_api", [])
        invented += [f"DDImage/{i}.h" for i in r["includes"]["invalid"]]
        invented += [f"DD::Image::{s}" for s in r["symbols"]["invalid"]]
    clean = sum(1 for r in results
                if not r["build"].get("invented_api")
                and not r["includes"]["invalid"]
                and not r["symbols"]["invalid"])
    built_but_failed = sum(1 for r in results
                           if r["produced_code"]
                           and r["build"].get("compiles") is not True)
    assert compiled + built_but_failed + no_code == n, \
        "summary does not reconcile against its own detail"
    return {
        "runs": n,
        "compiled": compiled,
        "built_but_failed": built_but_failed,
        "total_cost_usd": round(sum(r.get("cost_usd", 0.0) for r in results), 4),
        "mean_cost_usd": round(statistics.mean(
            [r.get("cost_usd", 0.0) for r in results]), 4),
        "total_output_tokens": sum(r.get("output_tokens", 0) for r in results),
        "total_input_tokens": sum(r.get("input_tokens", 0) for r in results),
        "compile_rate": round(compiled / n, 3),
        "runs_with_zero_invented_api": clean,
        "clean_rate": round(clean / n, 3),
        "invented_api_total": len(invented),
        "invented_api": sorted(set(invented)),
        "other_cpp_errors": sum(r["build"].get("other_cpp_errors", 0)
                                for r in results),
        "invalid_includes": bad_inc,
        "total_includes": tot_inc,
        "invalid_symbols": bad_sym,
        "total_symbols": tot_sym,
        "produced_no_code": no_code,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--case", default=None, help="substring filter")
    ap.add_argument("--arm", choices=["with", "without"], default=None)
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--out", type=pathlib.Path,
                    default=REPO / "evals" / "results" / "latest.json")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if shutil.which("claude") is None:
        print("claude CLI not on PATH", file=sys.stderr)
        return 1

    install = G.newest_install()

    work = REPO / "evals" / ".work"
    if work.exists():
        shutil.rmtree(work)
    # Both arms are bare directories -- the plugin needs no project setup, so
    # --plugin-dir is the entire difference between them.
    with_dir, without_dir = work / "with", work / "without"
    with_dir.mkdir(parents=True)
    without_dir.mkdir(parents=True)

    cases = sorted(CASES.glob("*.md"))
    if args.case:
        cases = [c for c in cases if args.case in c.name]
    if not cases:
        print("no cases matched", file=sys.stderr)
        return 1

    arms = [args.arm] if args.arm else ["without", "with"]
    per_arm: dict[str, list[dict]] = {a: [] for a in arms}
    detail = []

    for case in cases:
        prompt = case.read_text().strip() + "\n\n" + PREAMBLE
        for arm in arms:
            cwd = with_dir if arm == "with" else without_dir
            for i in range(args.runs):
                out = run_arm(prompt, cwd, arm == "with", args.model, args.timeout)
                res = G.grade(out["text"], install)
                res.update({"case": case.stem, "arm": arm, "run": i,
                            "cost_usd": out["cost_usd"],
                            "input_tokens": out["input_tokens"],
                            "output_tokens": out["output_tokens"]})
                per_arm[arm].append(res)
                detail.append(res)
                flag = "ok " if res["build"].get("compiles") else "BAD"
                extra = ""
                bad = res["includes"]["invalid"] + res["symbols"]["invalid"]
                if bad:
                    extra = "  invented: " + ", ".join(bad[:3])
                print(f"  [{flag}] {arm:<8} {case.stem:<20}{extra}", flush=True)
                if args.verbose and not res["build"].get("compiles"):
                    for e in res["build"].get("errors", [])[:3]:
                        print(f"          {e[:110]}")

    report = {"model": args.model, "runs_per_case": args.runs,
              "nuke": install.version, "cases": len(cases),
              "summary": {a: summarise(per_arm[a]) for a in arms},
              "detail": detail}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    print("\n" + "=" * 68)
    for arm in arms:
        s = report["summary"][arm]
        print(f"{arm:<8} compiles {s['compiled']}/{s['runs']} ({s['compile_rate']:.0%})"
              f"   no-invented-API {s['runs_with_zero_invented_api']}/{s['runs']}"
              f" ({s['clean_rate']:.0%})"
              f"   invented {s['invented_api_total']}"
              f"   other C++ errors {s['other_cpp_errors']}"
              f"   cost ${s['total_cost_usd']:.2f}"
              f" (mean ${s['mean_cost_usd']:.3f}/run)")
    for arm in arms:
        inv = report["summary"][arm]["invented_api"]
        if inv:
            print(f"\n  {arm} invented: " + ", ".join(inv[:12]))
    if len(arms) == 2:
        a, b = report["summary"]["without"], report["summary"]["with"]
        print(f"\n{'DELTA':<8} compiles {b['compile_rate'] - a['compile_rate']:+.0%}"
              f"   no-invented-API {b['clean_rate'] - a['clean_rate']:+.0%}"
              f"   invented {b['invented_api_total'] - a['invented_api_total']:+d}"
              f"   cost {b['mean_cost_usd'] - a['mean_cost_usd']:+.3f}/run")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
