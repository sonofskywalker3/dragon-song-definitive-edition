"""Runs the enemy attack recordings (dsde.enemy_anims) in parallel emulators and turns the logs into
timing.json, frames and a GIF per action under build/enemy_anims/<row>_<name>_<action>/.

Variants: `fast` (build/dsde.nds, speed setting pinned to Fast, a shot every 2nd frame of the first
recorded turn), `normal` (build/dsde.nds pinned to Normal) and `vanilla` (build/vanilla.nds), the last two
timing only. Rebuild build/dsde.nds from the tree first (`uv run python -m dsde.patches`): the Fast pin's
address comes from the current feature layout.

    uv run python -m dsde.enemy_anims_run run --workers 8            # everything
    uv run python -m dsde.enemy_anims_run run --only 020_Ice_Mongrel_a0_attack --variants fast
    uv run python -m dsde.enemy_anims_run report                     # markdown table from timing.json

A ROM with more features (the enemy action cuts of docs/plan-enemy-attacks.md) records into its own folder:

    uv run python -m dsde.patches --with enemy-sprite-speed enemy-quick-steps --output build/enemy_cut/all.nds
    uv run python -m dsde.enemy_anims_run run --variants fast --rom build/enemy_cut/all.nds \\
        --out build/enemy_anims_cut --with enemy-sprite-speed enemy-quick-steps
    uv run python -m dsde.enemy_anims_run report --out build/enemy_anims_cut --with enemy-quick-steps

Cut scripts live in ITCM; the logs show their address, and the analysis maps it back to the original
script (timing.json `script`; the cut copy's address is `cut_script`) and reads the cut copy's steps.
"""

import argparse
import json
import logging
import shutil
import struct
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from dsde.emu import START_SAVE, run_plan
from dsde.enemy_anims import ARM9_BIN, EnemyAction, Step, read_actions, read_steps
from dsde.enemy_anims_plans import SETUP_FORCED_ROWS, make_plan
from dsde.feat_enemy_moves import CUT_SETS, cut_scripts, label
from dsde.features import DEFAULT_FEATURES, FEATURES
from dsde.patching import layout_cave

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT = PROJECT_ROOT / "build" / "enemy_anims"
DSDE_ROM = PROJECT_ROOT / "build" / "dsde.nds"
VANILLA_ROM = PROJECT_ROOT / "build" / "vanilla.nds"
VARIANTS = ("fast", "normal", "vanilla")
SPEED_SETTING = {
    "fast": 1,
    "normal": 0,
}  # feat_battle_speed: 0 Normal, 1 Fast, 2 Faster
TURNS = 2
SHOT_EVERY = 2
GIF_FPS = 30
CUTOFF = 60  # frames on Fast, first action-script step to the last

# round states (battle work +0x2E, func_0202d22c)
RS_CAMERA = (5, 6)
RS_SCRIPT = 7  # the action script runs its steps
RS_INTERRUPT = (
    8,
    9,
    10,
    11,
)  # entered from a step that returns -2 (seen once: a counter, uncertain)
RS_DAMAGE_WAIT = 14

# func_02068034: Druid rows (0x84..0x87) using action 1 swap the skill's script for 0x02094F74 (two
# targets) or 0x02095174 (three)
DRUID_SCRIPTS = {row: (0x02094F74, 0x02095174) for row in range(132, 136)}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Setup:
    """Where a run reads its DE ROM and writes its folders, and the features that ROM was built with."""

    rom: Path = DSDE_ROM
    out: Path = OUT
    extra: tuple[str, ...] = ()
    # cut script address in ITCM -> (original script, cut steps)
    cuts: dict[int, tuple[int, list[Step]]] = field(default_factory=dict)

    @property
    def work(self) -> Path:
        return self.out / "_work"

    @property
    def features(self) -> list[str]:
        return [*DEFAULT_FEATURES, *self.extra]


def make_setup(rom: Path, out: Path, extra: tuple[str, ...]) -> Setup:
    by_name = {f.name: f for f in FEATURES}
    symbols = layout_cave([by_name[name] for name in [*DEFAULT_FEATURES, *extra]])
    cuts: dict[int, tuple[int, list[Step]]] = {}
    for prefix, cut_set in CUT_SETS.items():
        for script, raws in cut_scripts(cut_set).items():
            if label(prefix, script) not in symbols:
                continue
            steps = []
            for i, raw in enumerate(raws):
                flags, _, anim, sound, frames = struct.unpack("<IIhhh", raw[:14])
                steps.append(Step(i, flags, anim, sound, frames))
            cuts[symbols[label(prefix, script)]] = (script, steps)
    return Setup(rom, out, extra, cuts)


def speed_pin(variant: str, setup: Setup) -> str | None:
    if variant not in SPEED_SETTING:
        return None
    features = {f.name: f for f in FEATURES}
    symbols = layout_cave([features[name] for name in setup.features])
    return f"pin u8 {symbols['cave_speed_state']:#010x} {SPEED_SETTING[variant]}"


def signed(value: int) -> int:
    return value - (1 << 32) if value & 0x80000000 else value


def parse_rec(path: Path) -> list[dict]:
    """Turns from a .rec log: header and per-frame values."""
    turns: list[dict] = []
    for line in path.read_text().splitlines():
        words = line.split()
        if words[0] == "turn":
            turns.append(
                dict(actor=int(words[3]), row=int(words[5]), frames=[], ended=False)
            )
        elif words[0] == "end" and turns:
            turns[-1]["ended"] = True
        elif words[0] == "f" and turns:
            v = dict(zip(words[0::2], words[1::2]))
            turns[-1]["frames"].append(
                dict(
                    f=int(v["f"]),
                    rs=int(v["rs"]),
                    step=int(v["step"]),
                    script=int(v["scr"], 16),
                    x=signed(int(v["x"], 16)),
                    y=signed(int(v["y"], 16)),
                    z=signed(int(v["z"], 16)),
                    level=int(v["lvl"]),
                )
            )
    return turns


def analyse_turn(turn: dict, data: bytes, setup: Setup) -> dict:
    frames = turn["frames"]
    script_frames = [f for f in frames if f["rs"] == RS_SCRIPT]
    script = Counter(f["script"] for f in script_frames).most_common(1)
    logged = script[0][0] if script else 0
    script_addr, cut_steps = setup.cuts.get(logged, (logged, None))
    runs: list[list[int]] = []  # [step, frames]
    for f in script_frames:
        if runs and runs[-1][0] == f["step"]:
            runs[-1][1] += 1
        else:
            runs.append([f["step"], 1])
    if cut_steps is not None:
        static = {s.index: s for s in cut_steps}
    else:
        static = (
            {s.index: s for s in read_steps(data, script_addr)} if script_addr else {}
        )
    steps = []
    for index, count in runs:
        s = static.get(index)
        steps.append(
            dict(
                step=index,
                frames=count,
                kind=s.kind if s else "?",
                fixed_frames=s.frames if s and s.kind == "fixed" else None,
                flags=f"{s.flags:#010x}" if s else None,
            )
        )
    states = Counter(f["rs"] for f in frames)
    return dict(
        actor=turn["actor"],
        row=turn["row"],
        complete=turn["ended"],
        turn_frames=len(frames),
        camera_frames=sum(states[s] for s in RS_CAMERA),
        script=f"{script_addr:#010x}",
        cut_script=f"{logged:#010x}" if cut_steps is not None else None,
        script_frames=len(script_frames),
        interrupt_frames=sum(states[s] for s in RS_INTERRUPT),
        damage_wait_frames=states[RS_DAMAGE_WAIT],
        round_states={str(k): v for k, v in sorted(states.items())},
        steps=steps,
        speed_level=Counter(f["level"] for f in frames).most_common(1)[0][0]
        if frames
        else None,
        positions=[
            [f["f"], f["rs"], f["step"], f["x"], f["y"], f["z"]] for f in frames
        ],
    )


def make_gif(folder: Path) -> None:
    shots = sorted(folder.glob("frame_*.png"))
    if not shots:
        return
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(GIF_FPS),
            "-i", str(folder / "frame_%04d.png"),
            "-vf", "split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3",
            str(folder / "anim.gif"),
        ],
        check=True,
    )  # fmt: skip


def run_job(
    action: EnemyAction, variant: str, worker: int, data: bytes, setup: Setup
) -> dict:
    """One emulator run; returns the variant's timing and fills the action folder."""
    work = setup.work / f"w{worker}_{variant}"
    if work.exists():
        shutil.rmtree(work)
    (work / "rec").mkdir(parents=True)
    rom = work.parent / f"ea_w{worker}_{variant}.nds"
    source = VANILLA_ROM if variant == "vanilla" else setup.rom
    if (
        not rom.exists()
        or rom.stat().st_size != source.stat().st_size
        or rom.stat().st_mtime < source.stat().st_mtime
    ):
        shutil.copyfile(source, rom)
    # shots of every turn where the first one may be a scripted action (summary then picks the turn)
    shot_turns = (
        (TURNS if action.row in SETUP_FORCED_ROWS else 1) if variant == "fast" else 0
    )
    plan = work / "plan.plan"
    plan.write_text(
        make_plan(data, action, "r", speed_pin(variant, setup), TURNS, shot_turns)
    )
    log = run_plan(plan, rom, START_SAVE, work)
    folder = setup.out / action.key
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"run_{variant}.log").write_text(log)
    rec = work / "r.rec"
    shutil.copyfile(rec, folder / f"{variant}.rec") if rec.exists() else None
    for name in ("cmd", "end"):
        if (work / f"{name}.png").exists():
            shutil.copyfile(work / f"{name}.png", folder / f"{variant}_{name}.png")
    turns = (
        [analyse_turn(t, data, setup) for t in parse_rec(rec)] if rec.exists() else []
    )
    if variant == "fast":
        for old in folder.glob("frame_*.png"):
            old.unlink()
        chosen = summary(turns, action.row, action.script)
        number = turns.index(chosen) + 1 if chosen else 1
        for i, shot in enumerate(sorted((work / "rec").glob(f"r_t{number}_f*.png"))):
            shutil.copyfile(shot, folder / f"frame_{i:04d}.png")
        make_gif(folder)
    result = dict(variant=variant, turns=turns)
    (folder / f"timing_{variant}.json").write_text(json.dumps(result, indent=1))
    logger.info("%s %s: %s", action.key, variant, [t["script_frames"] for t in turns])
    return result


def merge(action: EnemyAction, setup: Setup) -> None:
    folder = setup.out / action.key
    merged = dict(
        key=action.key, rows=list(action.rows), name=action.name, action_index=action.index,
        flags=f"{action.flags:#010x}", extra=f"{action.extra:#x}", skill=action.skill,
        chance=action.chance, static_script=f"{action.script:#010x}", shot_every=SHOT_EVERY,
    )  # fmt: skip
    for variant in VARIANTS:
        path = folder / f"timing_{variant}.json"
        if path.exists():
            merged[variant] = json.loads(path.read_text())["turns"]
    (folder / "timing.json").write_text(json.dumps(merged, indent=1))


def run_all(
    actions: list[EnemyAction], variants: list[str], workers: int, setup: Setup
) -> None:
    data = ARM9_BIN.read_bytes()
    jobs = [(a, v) for a in actions for v in variants]
    free = list(range(workers))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = {}
        queue = list(jobs)
        while queue or pending:
            while queue and free:
                action, variant = queue.pop(0)
                worker = free.pop()
                pending[pool.submit(run_job, action, variant, worker, data, setup)] = (
                    worker,
                    action,
                )
            done = next(as_completed(pending))
            worker, action = pending.pop(done)
            free.append(worker)
            try:
                done.result()
            except (subprocess.TimeoutExpired, OSError, ValueError) as error:
                logger.error("%s failed: %s", action.key, error)
            merge(action, setup)


def summary(turns: list[dict] | None, row: int, script: int) -> dict | None:
    """Turn 1 (the recorded one) if it is a complete turn of the row that ran the expected script
    (any script when the static guess is 0), else the first later turn that is."""
    for t in turns or []:
        if t["row"] != row or not t["complete"] or t["script_frames"] == 0:
            continue
        if script == 0 or int(t["script"], 16) in {script, *DRUID_SCRIPTS.get(row, ())}:
            return t
    return None


def summarise(setup: Setup) -> list[dict]:
    """One record per action: the turn used for each variant (also written to summary.json)."""
    rows = []
    for action in read_actions(ARM9_BIN.read_bytes()):
        path = setup.out / action.key / "timing.json"
        t = json.loads(path.read_text()) if path.exists() else {}
        record = dict(
            key=action.key, rows=list(action.rows), name=action.name,
            action_index=action.index, flags=f"{action.flags:#010x}", extra=f"{action.extra:#x}",
            skill=action.skill, chance=action.chance, static_script=f"{action.script:#010x}",
        )  # fmt: skip
        for variant in VARIANTS:
            turn = summary(t.get(variant), action.row, action.script)
            turns = t.get(variant) or []
            record[variant] = (
                None
                if turn is None
                else dict(
                    turn=turns.index(turn) + 1,
                    script=turn["script"],
                    script_frames=turn["script_frames"],
                    turn_frames=turn["turn_frames"],
                    camera_frames=turn["camera_frames"],
                    damage_wait_frames=turn["damage_wait_frames"],
                    interrupt_frames=turn["interrupt_frames"],
                    steps=[[s["step"], s["frames"], s["kind"]] for s in turn["steps"]],
                )
            )
        fast = record["fast"]
        record["over_cutoff"] = None if fast is None else fast["script_frames"] > CUTOFF
        rows.append(record)
    (setup.out / "summary.json").write_text(json.dumps(rows, indent=1))
    return rows


def report(setup: Setup) -> str:
    lines = [
        "| Folder | Rows | Script | Fast | Normal | Vanilla | > 60 | Fast turn / camera / dmg wait "
        "| Fast steps (step:frames, a = animation, f = fixed) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in summarise(setup):
        fast, normal, vanilla = (r[v] for v in VARIANTS)
        cell = lambda s: str(s["script_frames"]) if s else "n/a"  # noqa: E731
        over = {True: "yes", False: "no", None: "?"}[r["over_cutoff"]]
        any_turn = fast or normal or vanilla
        script = any_turn["script"] if any_turn else "?"
        steps = " ".join(f"{i}:{n}{k[0]}" for i, n, k in fast["steps"]) if fast else ""
        extra = (
            f"{fast['turn_frames']} / {fast['camera_frames']} / {fast['damage_wait_frames']}"
            if fast
            else ""
        )
        lines.append(
            f"| {r['key']} | {','.join(map(str, r['rows']))} | {script} | {cell(fast)} | "
            f"{cell(normal)} | {cell(vanilla)} | {over} | {extra} | {steps} |"
        )
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.enemy_anims_run")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--only", nargs="*", help="folder names (row_name_action)")
    run.add_argument("--variants", default=",".join(VARIANTS))
    run.add_argument("--workers", type=int, default=6)
    report_parser = sub.add_parser("report")
    for p in (run, report_parser):
        p.add_argument(
            "--rom", type=Path, default=DSDE_ROM, help="DE ROM for fast/normal"
        )
        p.add_argument("--out", type=Path, default=OUT, help="output folder")
        p.add_argument(
            "--with", dest="extra", nargs="+", default=[],
            help="features the ROM has on top of the shipping set",
        )  # fmt: skip
    args = parser.parse_args()
    setup = make_setup(args.rom, args.out, tuple(args.extra))
    if args.command == "report":
        print(report(setup))
        return
    actions = read_actions(ARM9_BIN.read_bytes())
    if args.only:
        actions = [a for a in actions if a.key in args.only]
    run_all(actions, args.variants.split(","), args.workers, setup)


if __name__ == "__main__":
    main()
