"""Minimal gates on the ablation harness: the summary must reconcile against
its own detail (the lesson of eval Bug 3) and must carry the cost columns."""
import importlib.util
import sys


def load_runner(repo_root):
    p = repo_root / "evals" / "run_ablation.py"
    spec = importlib.util.spec_from_file_location("run_ablation", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_ablation"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run(produced, compiles, cost, tokens):
    return {"produced_code": produced,
            "build": {"compiles": compiles},
            "includes": {"total": 0, "invalid": []},
            "symbols": {"total": 0, "invalid": []},
            "cost_usd": cost, "input_tokens": tokens, "output_tokens": tokens}


def test_summary_reconciles_and_carries_cost(repo_root):
    mod = load_runner(repo_root)
    runs = [_run(True, True, 0.5, 1000),
            _run(True, False, 0.3, 800),
            _run(False, None, 0.1, 100)]
    s = mod.summarise(runs)
    assert s["runs"] == s["compiled"] + s["built_but_failed"] + s["produced_no_code"]
    assert s["compiled"] == 1 and s["built_but_failed"] == 1
    assert s["total_cost_usd"] == 0.9
    assert s["mean_cost_usd"] == 0.3
    assert s["total_output_tokens"] == 1900


def test_with_arm_is_plugin_dir_only(repo_root):
    text = (repo_root / "evals" / "run_ablation.py").read_text()
    assert "--plugin-dir" in text
    assert ".nuke-agent" not in text          # no dropped-setup reproduction
    assert "--output-format" in text and "json" in text
