"""The main RAM block's boot step, built whenever a chosen feature puts cave code in main RAM.

The startup code (0x020009B8) copies the autoloads, the main RAM block among them, with the caches already on
(init_cp15 at 0x02000A14 runs first) and main RAM cached write-back, so on real hardware some of the block can
still sit in the data cache, or in the write buffer, when the game first runs it. The copy loop ends at the empty
"autoload done" hook (0x02000A10, `bx lr`, after every block and before the program's variables are cleared).
That hook becomes a branch to cave_main_sync in ITCM (copied by then), which writes the whole data cache back
(the game's func_02004af8), drains the write buffer (func_02004ba4), and clears the instruction cache.
docs/plan-memory.md has the research.
"""

from dsde.patching import AsmPatch, CaveCode, Feature

AUTOLOAD_DONE = 0x02000A10  # bx lr, the startup code's autoload callback
BX_LR = 0xE12FFF1E
DC_STORE_ALL = 0x02004AF8  # clean every data cache line by index
DRAIN_WRITE_BUFFER = 0x02004BA4

SYNC_ASM = f"""
    push  {{r4, lr}}
    bl    {DC_STORE_ALL:#x}
    bl    {DRAIN_WRITE_BUFFER:#x}
    mov   r0, #0
    mcr   p15, 0, r0, c7, c5, 0
    pop   {{r4, lr}}
    bx    lr
"""


def main_ram_boot() -> Feature:
    return Feature(
        "main-ram-boot",
        (
            CaveCode(
                "cave_main_sync",
                SYNC_ASM,
                "main RAM block: write the data cache back, clear the instruction cache",
            ),
            AsmPatch(
                AUTOLOAD_DONE,
                AUTOLOAD_DONE + 4,
                BX_LR,
                BX_LR,
                "    b ${cave_main_sync}",
                "after the autoloads, sync the caches for the main RAM block",
            ),
        ),
    )


def uses_main_ram(feature: Feature) -> bool:
    return any(isinstance(p, CaveCode) and p.main for p in feature.patches)
