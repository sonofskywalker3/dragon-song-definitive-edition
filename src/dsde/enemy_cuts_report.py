"""Before/after table for the enemy action cuts (docs/plan-enemy-attacks.md).

Reads the Fast turn of every action from the original recordings (build/enemy_anims) and from one or more
cut recordings (folders written by `dsde.enemy_anims_run run --out ...`), using the same turn choice as the
runner's summary, and prints a markdown table: Fast script frames before, after each cut set, and whether
the last column is now under the cutoff.

    uv run python -m dsde.enemy_cuts_report build/enemy_cut/rec_sprite build/enemy_anims_cut
    uv run python -m dsde.enemy_cuts_report --steps build/enemy_anims_cut     # with the cut step lists
"""

import argparse
import json
import logging
import statistics
from pathlib import Path

from dsde.enemy_anims import ARM9_BIN, read_actions
from dsde.enemy_anims_run import CUTOFF, OUT, summary

logger = logging.getLogger(__name__)


def fast_turn(folder: Path, row: int, script: int) -> dict | None:
    path = folder / "timing.json"
    if not path.exists():
        return None
    return summary(json.loads(path.read_text()).get("fast"), row, script)


def steps_cell(turn: dict | None) -> str:
    if not turn:
        return ""
    return " ".join(f"{s['step']}:{s['frames']}{s['kind'][0]}" for s in turn["steps"])


def table(folders: list[Path], with_steps: bool) -> str:
    names = [f.name for f in folders]
    head = ["Action", "Script", "Before", *names, "< 60"]
    if with_steps:
        head.append(f"{names[-1]} steps")
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    totals: dict[str, list[int]] = {n: [] for n in ["Before", *names]}
    under = 0
    for action in read_actions(ARM9_BIN.read_bytes()):
        before = fast_turn(OUT / action.key, action.row, action.script)
        if before is None:
            continue
        afters = [fast_turn(f / action.key, action.row, action.script) for f in folders]
        cells = [str(before["script_frames"])]
        totals["Before"].append(before["script_frames"])
        for name, turn in zip(names, afters):
            cells.append(str(turn["script_frames"]) if turn else "n/a")
            if turn:
                totals[name].append(turn["script_frames"])
        last = afters[-1]
        ok = last is not None and last["script_frames"] <= CUTOFF
        under += ok
        row = [action.key, before["script"], *cells, "yes" if ok else "no"]
        if with_steps:
            row.append(steps_cell(last))
        lines.append("| " + " | ".join(row) + " |")
    medians = [
        f"{n}: median {statistics.median(v):.0f}, max {max(v)}, n {len(v)}"
        for n, v in totals.items()
        if v
    ]
    lines += ["", f"Under {CUTOFF} in {names[-1]}: {under}", *medians]
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.enemy_cuts_report")
    parser.add_argument("folders", nargs="+", type=Path)
    parser.add_argument(
        "--steps", action="store_true", help="add the last folder's steps"
    )
    args = parser.parse_args()
    print(table(args.folders, args.steps))


if __name__ == "__main__":
    main()
