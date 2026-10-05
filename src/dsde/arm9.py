"""Static analysis helpers for the ARM9 binary (extract/arm9/arm9.bin, loaded at 0x02000000).

The game reaches globals through literal pools, so Ghidra prints them as `DAT_<pool address>`
instead of the global itself. These helpers resolve pool words, find every function that loads an
address in a given range, disassemble functions with capstone, and write an annotated copy of the
Ghidra decompilation where each `DAT_xxxxxxxx` also shows the value stored there.

Usage:
    uv run python -m dsde.arm9 refs 0x020b464c 0x020b4658     # functions loading these addresses
    uv run python -m dsde.arm9 dis func_0201a404              # disassemble one function
    uv run python -m dsde.arm9 annotate                       # build/arm9_decomp_annot.c
"""

import argparse
import bisect
import logging
import re
import struct
from dataclasses import dataclass
from pathlib import Path

import capstone

log = logging.getLogger(__name__)

ARM9_BASE = 0x02000000
TEXT_END = 0x02088EF8
WORD = 4
THUMB_FLAG = "thumb"
DEFAULT_BIN = Path("extract/arm9/arm9.bin")
DEFAULT_SYMBOLS = Path("build/dsd/arm9/symbols.txt")
DEFAULT_DECOMP = Path("build/arm9_decomp.c")
DEFAULT_ANNOTATED = Path("build/arm9_decomp_annot.c")
SYMBOL_RE = re.compile(
    r"^(\S+) kind:function\((\w+),size=0x([0-9a-f]+)\) addr:0x([0-9a-f]+)"
)
DAT_RE = re.compile(r"DAT_([0-9a-f]{8})")


@dataclass(frozen=True)
class Function:
    name: str
    addr: int
    size: int
    thumb: bool

    @property
    def end(self) -> int:
        return self.addr + self.size


class Arm9:
    """The ARM9 image plus its dsd function symbols."""

    def __init__(
        self, bin_path: Path = DEFAULT_BIN, symbols_path: Path = DEFAULT_SYMBOLS
    ) -> None:
        self.data = bin_path.read_bytes()
        self.functions = sorted(_read_functions(symbols_path), key=lambda f: f.addr)
        self._starts = [f.addr for f in self.functions]
        self._by_name = {f.name: f for f in self.functions}

    def u32(self, addr: int) -> int:
        return struct.unpack_from("<I", self.data, addr - ARM9_BASE)[0]

    def contains(self, addr: int) -> bool:
        return ARM9_BASE <= addr < ARM9_BASE + len(self.data)

    def function_at(self, addr: int) -> Function | None:
        index = bisect.bisect_right(self._starts, addr) - 1
        if index < 0:
            return None
        func = self.functions[index]
        return func if addr < func.end else None

    def function(self, name_or_addr: str) -> Function:
        if name_or_addr in self._by_name:
            return self._by_name[name_or_addr]
        func = self.function_at(int(name_or_addr, 16))
        if func is None:
            raise KeyError(name_or_addr)
        return func

    def literal_refs(self, lo: int, hi: int) -> list[tuple[int, int, Function | None]]:
        """Every word-aligned code word whose value is in [lo, hi): (pool address, value, function)."""
        refs = []
        for addr in range(ARM9_BASE, TEXT_END, WORD):
            value = self.u32(addr)
            if lo <= value < hi:
                refs.append((addr, value, self.function_at(addr)))
        return refs

    def disassemble(self, func: Function) -> list[str]:
        mode = capstone.CS_MODE_THUMB if func.thumb else capstone.CS_MODE_ARM
        md = capstone.Cs(capstone.CS_ARCH_ARM, mode)
        md.skipdata = True  # keep going past inline literal pools and jump tables
        code = self.data[func.addr - ARM9_BASE : func.end - ARM9_BASE]
        lines = []
        for insn in md.disasm(code, func.addr):
            text = f"{insn.address:08x}  {insn.mnemonic:8s} {insn.op_str}"
            pool = _pc_relative_target(insn)
            if pool is not None and self.contains(pool):
                text += f"    ; [{pool:08x}] = {self.u32(pool):08x}"
            lines.append(text)
        return lines

    def annotate_decomp(
        self, src: Path = DEFAULT_DECOMP, dst: Path = DEFAULT_ANNOTATED
    ) -> None:
        """Copy the decompilation with each DAT_xxxxxxxx followed by /*=value*/."""

        def repl(match: re.Match[str]) -> str:
            addr = int(match.group(1), 16)
            if not self.contains(addr) or addr % WORD:
                return match.group(0)
            return f"{match.group(0)}/*={self.u32(addr):08x}*/"

        dst.write_text(
            DAT_RE.sub(repl, src.read_text(encoding="utf-8")), encoding="utf-8"
        )
        log.info("wrote %s", dst)


def _pc_relative_target(insn: capstone.CsInsn) -> int | None:
    """Address loaded by `ldr rX, [pc, #imm]`, if this is one."""
    match = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]", insn.op_str)
    if not insn.mnemonic.startswith("ldr") or match is None:
        return None
    offset = int(match.group(2), 0)
    is_thumb = insn.size == 2 or (insn.address & 1)
    pc = (insn.address + 4) & ~3 if is_thumb else insn.address + 8
    return pc + offset


def _read_functions(path: Path) -> list[Function]:
    funcs = []
    for line in path.read_text().splitlines():
        match = SYMBOL_RE.match(line)
        if match:
            name, mode, size, addr = match.groups()
            funcs.append(
                Function(name, int(addr, 16), int(size, 16), mode == THUMB_FLAG)
            )
    return funcs


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    refs = sub.add_parser(
        "refs", help="functions whose literal pools hold an address in [lo, hi)"
    )
    refs.add_argument("lo")
    refs.add_argument("hi")
    dis = sub.add_parser(
        "dis", help="disassemble a function by name or any address inside it"
    )
    dis.add_argument("func")
    sub.add_parser("annotate", help="write build/arm9_decomp_annot.c")
    args = parser.parse_args()
    arm9 = Arm9()
    if args.cmd == "refs":
        for pool, value, func in arm9.literal_refs(int(args.lo, 16), int(args.hi, 16)):
            log.info("%08x = %08x  in %s", pool, value, func.name if func else "?")
    elif args.cmd == "dis":
        for line in arm9.disassemble(arm9.function(args.func)):
            log.info(line)
    else:
        arm9.annotate_decomp()


if __name__ == "__main__":
    main()
