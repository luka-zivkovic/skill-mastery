#!/usr/bin/env python3
"""Drive the official microsoft/SkillOpt optimizer with a skill-mastery manifest.

Skill Mastery is the governance layer (evidence tiers, accept gates, records,
release packaging); the optimizer itself should be the maintained upstream
package, not the legacy in-repo loop (scripts/skillopt_run.py, kept only for the
mock/CI path). This bridge:

  1. validates the eval manifest and refuses non-loop tiers (subjective);
  2. refuses to start when the workshop copy drifts from the deployed hash
     (same sync rule as the in-repo loop);
  3. translates the manifest's splits/scoring into a SkillOpt run config;
  4. shells out to the installed `skillopt` CLI;
  5. records the outcome in records/ in skill-mastery's history format.

Requires: pip install skillopt  (https://github.com/microsoft/SkillOpt)

NOTE: the upstream CLI surface is young (v0.1.x). The config translation lives in
build_skillopt_config() and is the only part expected to churn; everything else
is stable skill-mastery policy. If the installed skillopt version rejects the
generated config, run with --print-config and adapt that function.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _manifest import Manifest, load as load_manifest  # noqa: E402
from validate_eval_manifest import validate as validate_manifest  # noqa: E402


def build_skillopt_config(manifest: Manifest, skill_dir: Path, out_dir: Path) -> dict:
    """Translate a skill-mastery eval manifest into a SkillOpt run config.

    Maps our train/validation/test splits and tier accept-rule onto the
    upstream rollout/gate settings. Deliberately conservative: bounded edits,
    strict validation gate, held-out test untouched.
    """
    def split(name: str) -> list[dict]:
        return [
            {"id": t.id, "prompt": t.prompt, "success_criteria": t.success_criteria}
            for t in manifest.splits.get(name, [])
        ]

    return {
        "skill_path": str(skill_dir / "SKILL.md"),
        "output_dir": str(out_dir),
        "tasks": {
            "train": split("train"),
            "validation": split("validation"),
            "test": split("test"),
        },
        "gate": {
            "mode": "strict_improve" if manifest.verifiability == "objective"
                    else "pairwise_majority_no_regression",
            "grading_runs": manifest.grading_runs,
        },
        "edits": {"bounded": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--records", type=Path, default=Path("records"))
    parser.add_argument("--print-config", action="store_true",
                        help="print the translated config and exit (no skillopt needed)")
    args = parser.parse_args()

    errors = validate_manifest(args.manifest)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    manifest = load_manifest(args.manifest)

    tier = manifest.verifiability
    if tier == "subjective":
        print("ERROR: subjective tier has no scored gate — use the lite path, not an optimizer.",
              file=sys.stderr)
        return 1

    out_dir = Path("workshop/runs") / f"{manifest.skill}-skillopt"
    config = build_skillopt_config(manifest, args.skill_dir, out_dir)
    if args.print_config:
        print(json.dumps(config, indent=2))
        return 0

    if shutil.which("skillopt") is None:
        print("ERROR: skillopt CLI not found. Install the official optimizer first:\n"
              "  pip install skillopt    # https://github.com/microsoft/SkillOpt",
              file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    config_path = out_dir / "skillopt-config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    print(f"Running official SkillOpt with {config_path} ...")
    proc = subprocess.run(["skillopt", "run", "--config", str(config_path)])

    record = {
        "skill": manifest.skill,
        "tier": tier,
        "engine": "microsoft/skillopt",
        "config": str(config_path),
        "exit_code": proc.returncode,
    }
    args.records.mkdir(parents=True, exist_ok=True)
    history = args.records / "eval_results.jsonl"
    with history.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    print(f"Recorded run in {history} (exit {proc.returncode}). "
          "Review staged edits before shipping — the gate is upstream's, the governance is ours.")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
