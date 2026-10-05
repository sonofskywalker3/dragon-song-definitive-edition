"""Code patches for arm9.bin and the build that turns extract/ into a patched ROM.

Every patch states the bytes it expects to replace, so a patch applied to the wrong
build or the wrong address fails loudly instead of corrupting the game.
"""

import argparse
import logging
import shutil
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

from keystone import KS_ARCH_ARM, KS_MODE_ARM, Ks

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTRACT = PROJECT_ROOT / "extract"
MOD_EXTRACT = PROJECT_ROOT / "build" / "mod_extract"
DSD = PROJECT_ROOT / "tools" / "dsd.exe"
OUTPUT_ROM = PROJECT_ROOT / "build" / "dsde.nds"
ARM9_BASE = 0x02000000

logger = logging.getLogger(__name__)


class PatchError(RuntimeError):
    """Raised when the bytes at a patch site are not what the patch expects."""


@dataclass(frozen=True)
class Patch:
    """Replace one 32-bit ARM instruction in arm9.bin."""

    addr: int
    old: int
    new: int
    note: str


@dataclass(frozen=True)
class AsmPatch:
    """Overwrite the dead code block addr..end (exclusive) with new ARM code.

    first and last are the original words at addr and end - 4, checked before writing.
    """

    addr: int
    end: int
    first: int
    last: int
    asm: str
    note: str


@dataclass(frozen=True)
class Feature:
    """A named group of patches that together make one design change."""

    name: str
    patches: tuple[Patch | AsmPatch, ...]


# Field running, see docs/re-field-battle.md section 1. The run state lives in the player's
# 8-bit counter at +0x40 bits 5..12 (the old HP drain counter): 0 = ready, 1..RUN_TICKS =
# running, then cooldown until RUN_TICKS + COOLDOWN_TICKS. One tick = 2 frames at 60 fps.
FRAMES_PER_TICK = 2
RUN_TICKS = 90  # 3 seconds
COOLDOWN_TICKS = 90  # 3 seconds
FRAME_COUNTER = 0x020B05BC
TIMED_RUN_BODY_ADDR = 0x020251AC
TIMED_RUN_EXIT = 0x02024C58
DPAD_MASK = 0xF0
# Bits 5..12 (0x1FE0) is not an ARM immediate, so it is cleared in two parts
COUNTER_MASK_HIGH = 0x1FC0
COUNTER_MASK_LOW = 0x20

# Part 1 sits in the freed too-tired check block: load the run state, then jump to part 2.
TIMED_RUN_ASM_ENTRY = f"""
    ldr   r1, [r2]
    mov   r3, r1, lsl #19
    mov   r3, r3, lsr #24
    ldr   r0, [sp, #8]
    ldr   r12, frame_counter
    ldrh  r12, [r12]
    b     {TIMED_RUN_BODY_ADDR:#x}
frame_counter:
    .word {FRAME_COUNTER:#x}
"""

# Part 2 sits in the freed HP drain block. In: r0 = B held, r1 = player flags, r2 = &flags,
# r3 = run state, r5 = held keys, r12 = frame counter.
TIMED_RUN_ASM_BODY = f"""
    cmp   r3, #0
    bne   active
    cmp   r0, #0
    tstne r5, #{DPAD_MASK:#x}
    movne r3, #1
    b     store
active:
    cmp   r3, #{RUN_TICKS}
    bhi   tick
    cmp   r0, #0
    moveq r3, #{RUN_TICKS + 1}
    beq   store
tick:
    tst   r12, #{FRAMES_PER_TICK - 1}
    addeq r3, r3, #1
    cmp   r3, #{RUN_TICKS + COOLDOWN_TICKS}
    movhi r3, #0
store:
    bic   r1, r1, #{COUNTER_MASK_HIGH:#x}
    bic   r1, r1, #{COUNTER_MASK_LOW:#x}
    orr   r1, r1, r3, lsl #5
    str   r1, [r2]
    sub   r0, r3, #1
    cmp   r0, #{RUN_TICKS}
    movlo r0, #1
    movhs r0, #0
    str   r0, [sp, #8]
    b     {TIMED_RUN_EXIT:#x}
"""

# Branch encodings: 0xEA000000 | ((target - (addr + 8)) >> 2).
NO_RUN_HP_COST = Feature(
    "no-run-hp-cost",
    (
        Patch(
            0x020251A8,
            0x1A00001E,
            0xEA00001E,
            "bne -> b: skip the drain counter and 180-frame HP drain",
        ),
        Patch(
            0x02024BF8,
            0x0A000016,
            0xEA000016,
            "beq -> b: skip the HP <= 1/3 too-tired check",
        ),
    ),
)

TIMED_RUN = Feature(
    "timed-run",
    (
        Patch(
            0x020251A8,
            0x1A00001E,
            0xEA00001E,
            "bne -> b: skip the drain counter and 180-frame HP drain",
        ),
        AsmPatch(
            0x02024BF8,
            0x02024C58,
            0x0A000016,
            0xBAFFFFEA,
            TIMED_RUN_ASM_ENTRY,
            "load run state",
        ),
        AsmPatch(
            TIMED_RUN_BODY_ADDR,
            0x02025228,
            0xE5902000,
            0xEB013188,
            TIMED_RUN_ASM_BODY,
            "3 s run, 3 s cooldown",
        ),
    ),
)

FEATURES: tuple[Feature, ...] = (NO_RUN_HP_COST, TIMED_RUN)
DEFAULT_FEATURES: tuple[str, ...] = (TIMED_RUN.name,)


def _check_word(arm9: bytearray, feature: Feature, addr: int, expected: int) -> None:
    (current,) = struct.unpack_from("<I", arm9, addr - ARM9_BASE)
    if current != expected:
        raise PatchError(
            f"{feature.name} @ {addr:#010x}: expected {expected:#010x}, found {current:#010x}"
        )


def assemble(asm: str, addr: int) -> bytes:
    """Assemble ARM code for the given load address."""
    encoding, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(asm, addr)
    return bytes(encoding)


def apply_arm9(arm9: bytearray, feature: Feature) -> None:
    """Apply every patch of a feature to an arm9.bin image in place."""
    for patch in feature.patches:
        if isinstance(patch, AsmPatch):
            _check_word(arm9, feature, patch.addr, patch.first)
            _check_word(arm9, feature, patch.end - 4, patch.last)
            code = assemble(patch.asm, patch.addr)
            if len(code) > patch.end - patch.addr:
                raise PatchError(
                    f"{feature.name}: {len(code)} bytes do not fit in {patch.end - patch.addr}"
                )
            arm9[patch.addr - ARM9_BASE : patch.addr - ARM9_BASE + len(code)] = code
            logger.info(
                "%s @ %#010x: %s (%d bytes)",
                feature.name,
                patch.addr,
                patch.note,
                len(code),
            )
            continue
        offset = patch.addr - ARM9_BASE
        (current,) = struct.unpack_from("<I", arm9, offset)
        if current != patch.old:
            raise PatchError(
                f"{feature.name} @ {patch.addr:#010x}: expected {patch.old:#010x}, found {current:#010x}"
            )
        struct.pack_into("<I", arm9, offset, patch.new)
        logger.info("%s @ %#010x: %s", feature.name, patch.addr, patch.note)


def build(feature_names: list[str], output: Path = OUTPUT_ROM) -> Path:
    """Copy extract/, apply the named features, and build a ROM."""
    wanted = {f.name: f for f in FEATURES}
    unknown = set(feature_names) - wanted.keys()
    if unknown:
        raise PatchError(f"unknown features: {sorted(unknown)}")
    if MOD_EXTRACT.exists():
        shutil.rmtree(MOD_EXTRACT)
    shutil.copytree(EXTRACT, MOD_EXTRACT)
    arm9_path = MOD_EXTRACT / "arm9" / "arm9.bin"
    arm9 = bytearray(arm9_path.read_bytes())
    for name in feature_names:
        apply_arm9(arm9, wanted[name])
    arm9_path.write_bytes(arm9)
    subprocess.run(
        [
            str(DSD),
            "rom",
            "build",
            "-c",
            str(MOD_EXTRACT / "config.yaml"),
            "-o",
            str(output),
        ],
        check=True,
    )
    logger.info("built %s with %s", output, ", ".join(feature_names) or "no features")
    return output


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(prog="dsde.patches")
    parser.add_argument(
        "features", nargs="*", help="feature names; default is all of them"
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_ROM)
    args = parser.parse_args()
    build(args.features or list(DEFAULT_FEATURES), args.output)


if __name__ == "__main__":
    main()
