"""Disassembler for the event scripts in script.dat (build/unpacked/script/NNN.bin).

The interpreter is func_020418ac. Each instruction starts with a u16 opcode; the handler table at
0x020A3EE8 has 83 entries of {handler, yield flag}. A script file starts with op 0x02 (jump) to its
code. Ops 0x13/0x14/0x15 carry a variable-length flag list, op 0x35 a variable-length payload.

Usage:
    uv run python -m dsde.script build/unpacked/script/010.bin            # linear listing
    uv run python -m dsde.script build/unpacked/script/010.bin --text     # with message text
    uv run python -m dsde.script build/unpacked/script/010.bin --reach    # only code reachable from the entry
"""

import argparse
import logging
import struct
from pathlib import Path

log = logging.getLogger(__name__)

FIXED_LENGTHS = {
    0x00: 4,
    0x01: 8,
    0x02: 8,
    0x03: 8,
    0x04: 4,
    0x05: 12,
    0x06: 12,
    0x07: 12,
    0x08: 12,
    0x09: 12,
    0x0A: 12,
    0x0B: 8,
    0x0C: 8,
    0x0D: 16,
    0x0E: 16,
    0x0F: 8,
    0x10: 8,
    0x11: 8,
    0x12: 8,
    0x16: 4,
    0x17: 4,
    0x18: 4,
    0x19: 4,
    0x1A: 4,
    0x1B: 4,
    0x1C: 4,
    0x1D: 8,
    0x1E: 4,
    0x1F: 4,
    0x20: 4,
    0x21: 4,
    0x22: 8,
    0x23: 4,
    0x24: 8,
    0x25: 8,
    0x26: 12,
    0x27: 12,
    0x28: 4,
    0x29: 16,
    0x2A: 16,
    0x2B: 4,
    0x2C: 8,
    0x2D: 12,
    0x2E: 8,
    0x2F: 4,
    0x30: 8,
    0x31: 12,
    0x32: 8,
    0x33: 8,
    0x34: 8,
    0x36: 4,
    0x37: 12,
    0x38: 4,
    0x39: 16,
    0x3A: 8,
    0x3B: 8,
    0x3C: 8,
    0x3D: 20,
    0x3F: 4,
    0x40: 12,
    0x41: 4,
    0x42: 12,
    0x43: 4,
    0x44: 8,
    0x45: 4,
    0x46: 12,
    0x47: 12,
    0x48: 4,
    0x49: 8,
    0x4A: 16,
    0x4B: 8,
    0x4C: 8,
    0x4D: 8,
    0x4E: 12,
    0x4F: 8,
    0x50: 16,
    0x51: 8,
    0x52: 8,
}
OP_JUMP = 0x02
OP_CALL = 0x03
OP_RET = 0x04
OP_IF_CMP_CALL = frozenset({0x0D, 0x0E})
OP_MSG = 0x0F
OP_FLAG_LISTS = frozenset({0x13, 0x14, 0x15})
OP_SHORT_ARG = frozenset({0x19, 0x1A, 0x1B, 0x1C, 0x21})
OP_END = 0x20
OP_YES_NO = 0x31
OP_VARIABLE = 0x35
STOP_OPS = frozenset({OP_JUMP, OP_RET, OP_END, OP_YES_NO})
NAMES = {
    0x00: "yield",
    OP_JUMP: "jump",
    OP_CALL: "call",
    OP_RET: "ret",
    0x05: "var_set",
    0x0D: "if_cmp_call",
    0x0E: "if_cmp_call",
    OP_MSG: "msg",
    0x13: "if_all_set_goto",
    0x14: "if_none_set_goto",
    0x15: "if_any_set_goto",
    0x19: "set_flag",
    0x1A: "clear_flag",
    0x1B: "party_join",
    0x1C: "party_leave",
    OP_END: "end",
    0x21: "give_money",
    OP_YES_NO: "yes_no",
}
TEXT_SPACE = 0x00
TEXT_UPPER = range(0x02, 0x1C)
TEXT_LOWER = range(0x3A, 0x54)
TEXT_END = 0xFF
TEXT_PREVIEW = 120


class ScriptError(ValueError):
    """Raised when the disassembler meets an unknown opcode (desync or data)."""


def decode_text(data: bytes) -> str:
    """Decode game text up to the 0xFF terminator; unknown bytes show as <xx>."""
    out = []
    for c in data:
        if c == TEXT_END:
            break
        if c == TEXT_SPACE:
            out.append(" ")
        elif c in TEXT_UPPER:
            out.append(chr(ord("A") + c - TEXT_UPPER.start))
        elif c in TEXT_LOWER:
            out.append(chr(ord("a") + c - TEXT_LOWER.start))
        else:
            out.append(f"<{c:02x}>")
    return "".join(out)


def op_length(data: bytes, pc: int) -> int:
    op = struct.unpack_from("<H", data, pc)[0]
    if op in OP_FLAG_LISTS:
        return 8 + 4 * struct.unpack_from("<H", data, pc + 2)[0]
    if op == OP_VARIABLE:
        return 8 + ((data[pc + 2] + 1) & ~1) * 2
    if op not in FIXED_LENGTHS:
        raise ScriptError(f"unknown op {op:#x} at {pc:#x}")
    return FIXED_LENGTHS[op]


def branch_targets(data: bytes, pc: int) -> list[int]:
    op = struct.unpack_from("<H", data, pc)[0]
    if op in (OP_JUMP, OP_CALL) or op in OP_FLAG_LISTS:
        return [struct.unpack_from("<I", data, pc + 4)[0]]
    if op in OP_IF_CMP_CALL:
        return [struct.unpack_from("<I", data, pc + 12)[0]]
    if op == OP_YES_NO:
        return list(struct.unpack_from("<II", data, pc + 4))
    return []


def format_op(data: bytes, pc: int, with_text: bool) -> str:
    op = struct.unpack_from("<H", data, pc)[0]
    length = op_length(data, pc)
    extra = ""
    if op in OP_FLAG_LISTS:
        count = struct.unpack_from("<H", data, pc + 2)[0]
        target = struct.unpack_from("<I", data, pc + 4)[0]
        flags = struct.unpack_from(f"<{count}I", data, pc + 8)
        extra = f"flags={[hex(f) for f in flags]} -> {target:#x}"
    elif op in OP_SHORT_ARG:
        extra = f"{struct.unpack_from('<h', data, pc + 2)[0]:#x}"
    elif op in (OP_JUMP, OP_CALL):
        extra = f"-> {struct.unpack_from('<I', data, pc + 4)[0]:#x}"
    elif op == OP_MSG and with_text:
        offset = struct.unpack_from("<I", data, pc + 4)[0]
        if offset < len(data):
            extra = repr(decode_text(data[offset : offset + TEXT_PREVIEW]))
    return f"{pc:05x}: {op:02x} {NAMES.get(op, ''):16s} {data[pc : pc + length].hex()} {extra}"


def linear(data: bytes) -> list[int]:
    """Instruction addresses from the code start until the first unknown op."""
    pc = struct.unpack_from("<I", data, 4)[0]
    addrs = []
    while pc + 2 <= len(data):
        try:
            length = op_length(data, pc)
        except ScriptError:
            log.warning("desync at %#x", pc)
            break
        addrs.append(pc)
        pc += length
    return addrs


def reachable(data: bytes) -> list[int]:
    """Instruction addresses reachable from the entry jump (misses entry points nothing jumps to)."""
    seen: set[int] = set()
    work = [0]
    while work:
        pc = work.pop()
        while pc + 2 <= len(data) and pc not in seen:
            try:
                length = op_length(data, pc)
            except ScriptError:
                log.warning("unknown op at %#x", pc)
                break
            seen.add(pc)
            work.extend(t for t in branch_targets(data, pc) if t < len(data))
            if struct.unpack_from("<H", data, pc)[0] in STOP_OPS:
                break
            pc += length
    return sorted(seen)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--text", action="store_true", help="show message text")
    parser.add_argument(
        "--reach", action="store_true", help="follow branches instead of a linear sweep"
    )
    args = parser.parse_args()
    data = args.path.read_bytes()
    for pc in reachable(data) if args.reach else linear(data):
        log.info(format_op(data, pc, args.text))


if __name__ == "__main__":
    main()
