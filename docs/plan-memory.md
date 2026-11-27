# Room for new code and new text

Status: research done, waiting for Jeff's yes before building (2026-11-26).

## Short answer

- **Code:** the game leaves about **255 KB of main RAM unused**, between the end of its 2 MB heap and the sound
  processor's program. Nothing touches it, measured in the emulator from power-on through the intro, the field
  menu, a normal battle, a boss fight, map changes, a shop, Gad's Express, and saving to the card. We can copy our code there at boot with a third
  "autoload", the same mechanism that already copies our code into the fast ITCM. We use the lower
  **190 KB** of it (0x02340600..0x0236FFFF): one 3DS loader mode is known to park its own code at 0x02370000.
  That is 6 times the ITCM cave, enough for party chat and everything planned after it.
- **Text:** text is not short of room. Every line of every script at 1.5 times its length fits, and so would
  twice the length, once the text tool rebuilds a script's text instead of adding new copies after the old. Scripts are loaded into the heap at exactly their size, and a map has about 750 KB of the
  heap free. The real limits are the 30-character line width of a text box (a layout rule, not memory) and,
  for the menus' item and battle words, tables packed into the game's program, which can move to the new block.

## 1. Room for code

### Where memory goes today

| Range | What is there |
| --- | --- |
| 0x01FF8000..0x01FFFFFF (32 KB) | ITCM, the fast memory. The game uses 0x2E0 bytes; our cave holds the rest. The full Retold build leaves about 560 bytes free. |
| 0x02000000..0x020AC460 | The game's program and its fixed data |
| 0x020AC460..0x02140500 | The program's variables (bss), including the 512 KB sound heap |
| 0x02140500..0x02140540 | Heap bookkeeping |
| 0x02140540..0x02340540 | Heap 0: **exactly 2 MB**, everything the game loads (maps, scripts, battle graphics) |
| **0x02340540..0x0237FFFF** | **Unused: 260,800 bytes** |
| 0x02380000..0x023A64AC | The ARM7 (sound and touch processor) program as loaded |
| 0x023C0000..0x023D8568 | The ARM7's relocated code and variables (its autoload to 0x027C0000, the same RAM) |

How we know the heap stops at 0x02340540: `main` (0x02000B24) sets up the main memory area with its start at
0x02140500 and its end at 0x023C0000 (func_02004f74 / func_02004db0), takes **a fixed 2 MB** from the start
(`func_02004c18(0, 0x200000, 0x20)`), and makes heap 0 from exactly that 2 MB. It is the only allocation from
that area; nothing ever takes memory from its end, and the game has only that one heap. The emulator agrees: the
area's start pointer (0x027FFDA0) reads 0x02340540 after boot. So the heap never grows into the gap, however full
it gets. The area's end, 0x023C0000, runs past the ARM7's start, but nothing uses that part.

### Checked in the emulator (Retold build)

The new plan commands `fill` and `changed` paint the range 0x02340600..0x0237FFFF with 0xA5 and later list every
byte that no longer holds it. `heap`, `heapwatch`, and `heapmin` read heap 0's free list.

| Plan | Covers | Bytes changed in the gap | Heap low point (free) |
| --- | --- | --- | --- |
| mem_free_b | power-on, title, New Game, the whole intro to Jian's room (16,000 frames) | 0 | |
| mem_free_a / mem_heap_a | save load, field menu tour, Delrich Temple battle and results, a map change | 0 | field 712 KB, battle 201 KB |
| mem_free_c / mem_heap_c | scripted Red Dragon boss fight and its result pages | 0 | 174 KB |
| mem_free_test_field_menu_save | Select-to-Save: a save written to the card | 0 | 716 KB |
| mem_free_test_mp_shop | a town's item shop: open, buy | 0 | 522 KB |
| mem_free_test_gad_accept | Gad's Express: accept a job | 0 | 617 KB |

The gap was also all zeros when the save finished loading: nothing put anything there at boot.

Not yet checked: the ending and **real hardware**.
Emulators do not show two things that only a real DS or the 3DS can: whether a loader (nds-bootstrap on the
3DS, a flash cart's menu) keeps its own code in that range, and the cache issue below.

Nothing in the program (ARM9 or ARM7) holds an address inside the gap, so no fixed pointer leads there. That
plus the allocation trace plus the emulator runs make the gap very likely unused, though no test can prove that
a computed address or a transfer never reaches it.

**Loaders.** nds-bootstrap (the 3DS and DSi loader) in its "B4DS" mode, used on a DS or DS Lite with a flash
cart, copies 0x2800 bytes of its own code to **0x02370000..0x023727FF** before the game starts, and clears that
range later in startup, after our block is copied. A block reaching 0x02370000 would be damaged in that mode.
Its usual 3DS and DSi locations (0x027FC000 and up) are outside the gap. So the block stays below 0x02370000,
which leaves **195,072 bytes** from 0x02340600. Other flash-cart menus are unknown; the 3DS (Jeff's console)
is the one to test, with saving, sleep and wake, and a soft reset.

### Options

| Option | Room | Cost to build and test | Risk |
| --- | --- | --- | --- |
| **A. Third autoload into the gap** (recommended) | **~190 KB**, one block | Medium: ndsrom.py, linker.py, the dsd config, patching.py (a second cave), a cache flush at boot, the installer comparison, a 3DS test | Low in emulators (measured); real hardware needs one test |
| B. Reuse dead vanilla code we bypass (mic-blow detector func_0206bafc is 192 bytes; the Virtue clock, old L/R fast-forward, HP drain) | A few hundred bytes per piece, roughly 1 to 3 KB in all, scattered | High per byte: each piece must be proved dead in both editions and with every switch | Low, but too small and too scattered for party chat (3,200 bytes) |
| C. Load rarely used code from a file when needed (overlay-like) | As much as we like | High: a loader, a buffer from the heap (only 174 KB free in a boss fight), timing | Medium |

### How option A works

- **The autoload.** The program's header (module params at arm9 + 0xB00) lists blocks the startup code copies out
  of the program image before the game starts: today the ITCM block and a 96-byte DTCM block. A third entry,
  address 0x02340600 with our code as its data, is copied by the same startup loop (0x020009B8), before the
  game's own code runs and before the heap exists. The block is only as big as the code in it; unused room
  costs nothing in the ROM.
- **The cache.** The DS's main RAM is cached, and the startup copy writes through the data cache, so on real
  hardware a few bytes of the new block could still sit in the cache when the game first runs them. The startup
  code ends by jumping to an empty "autoload done" hook (0x02000A10, `bx lr`, reached after every block is
  copied and before the program's variables are cleared). We replace it with a `b` (not `bl`, which would lose
  the return address) to a few instructions in ITCM that write the data cache back (the game's own routine at
  0x02004AF8 cleans it all), drain the write buffer (0x02004BA4), and clear the instruction cache, then return.
  That runs once, at boot. Block sizes stay multiples of 4, as the copy loop moves whole words.
- **Fencing it off.** The main area's end pointer still says 0x023C0000, so the game could in theory hand out the
  gap. It never does, but the same boot hook sets the end to 0x02340540 (0x027FFDC4), so nothing ever can.
- **Speed.** Code in main RAM runs slower than in ITCM (it goes through the cache). Per-frame hooks that run in
  every frame of a battle stay in ITCM; bulky code and data that runs now and then moves out.
- **Tried:** a Retold build with a 256-byte test block added this way (config.yaml `unknown_autoloads:` with
  `- index: 2`, `bin:`, `config:`; the block's yaml has `kind: !Unknown 2`) builds with dsd, ndsrom.py reads
  three autoloads back, and in the emulator the game boots, loads a save, and the block's bytes are in RAM at
  its address while the heap still starts and ends where it did (emu/plans/mem_t3.plan).
- **Build tools.** dsd 0.12 supports extra autoloads (`unknown_autoloads` in config.yaml). ndsrom.py already
  reads and rewrites the autoload list; it needs to write a third entry. linker.py and patching.py lay out
  two caves instead of one; each `CaveCode` names its cave, ITCM by default. The installer's result must still
  equal the dsd build (docs/plan-installer.md section 5).

### What moves first

1. **Party chat**: its entry table (now in ITCM) and its selection code, about 3,200 bytes plus the table. Its two
   start hooks and the per-frame figure pulse are small and can stay in ITCM or move; they run once per chat
   or once per frame in the field only.
2. **Large tables now in ITCM**: skill tables, card tables, guidebook data. Moving them back frees ITCM for
   battle code that runs every frame.
3. **Later text tables** (section 2.3), if the menus' words get longer.

With these moves the ITCM cave goes from 560 bytes free to several KB free, and the new block has room to spare
for years of features.

## 2. Room for text

### 2.1 Event scripts (all dialogue)

All dialogue lives in script.dat: 28 scripts, one per group of maps (and 018 for party chat). Each script holds
its own text, one byte per character, after a jump at its start.

- **Where a script goes when it loads:** func_02041a68 asks how big the script is and takes exactly that much
  from heap 0 (func_02005298), in one piece. Message offsets and jumps are 32-bit, so there is no size field to
  outgrow. The one fixed buffer is the 128 KB the file reader keeps for the compressed entry (func_0201A818);
  compressed scripts are under 10 KB, so that is far off. The script stays loaded while the map is up, battles included (checked: the same buffer,
  0x02280C20, before and during a battle).
- **Sizes:** the largest script is 004 at 31,608 bytes (25,620 of them text); all 28 together are 335 KB, 239 KB
  of it text. The Retold build adds about 4 KB so far.

| Script | Size now | Text | Every line 1.5 times longer | Twice as long |
| --- | --- | --- | --- | --- |
| 004 | 31,608 | 25,620 | 44,418 | 57,228 |
| 001 | 30,048 | 21,676 | 40,886 | 51,724 |
| 018 (party chat) | 25,620 | 20,764 | 36,002 | 46,384 |
| 009 | 25,828 | 19,984 | 35,820 | 45,812 |
| 021 | 27,064 | 14,556 | 34,342 | 41,620 |

These sizes assume the new text replaces the old. Today's text tool (feat_text.py) leaves an edited line's old
text in place and adds the new one at the end of the script, which is fine for a few lines but for a full
rewrite would keep both: script 004 would reach about 70 KB at 1.5 times and 83 KB at twice. For the rewrite the
tool should rebuild each script's text block from the new lines (every message op already points at its text by
offset, so this is a contained change).

- **Room for it:** a map leaves about 750 KB of the heap free, so the field has room for scripts many times their
  size. The tight spot is battle, because the map's script stays loaded: a boss fight went down to 174 KB free.
  Making script 004 1.5 times longer takes 13 KB of that; twice as long takes 26 KB (38 KB and 51 KB with
  today's append-only tool). The script needs one unbroken block, so what counts is the largest free block,
  which `heapmin` reports (174 KB at the boss fight's low point). Party chat (018) loads as a
  second script, but only in the field.
- **ROM:** about 7 MB free at the end; script.dat is 167 KB compressed. Not a limit.
- **Verdict:** rewriting every line at 1.5 times the length fits with nothing changed. The limits that matter are
  on screen: a text box wraps at 30 characters (feat_text.py), so longer lines mean more boxes, which the
  build's text tools already handle by putting a changed message at the end of its script.
- **To watch:** the worst battles we have not measured (big bosses with a full party). Before the rewrite ships,
  run `heapwatch` through the largest boss fights with the longest scripts loaded; keep 50 KB spare.

### 2.2 Menu descriptions (sysmenupack)

Item and card descriptions are sysmenupack 058 (26,276 bytes) and 057 (20,644). They load into the heap when the
menu opens (the field menu's low point was 712 KB free). Their strings are found through 16-bit offsets
from the string start, so the text can grow to about 64 KB, 2.4 times 058's. Memory is not a limit, but the
drawing code may be: a description draw path uses a fixed 61-byte stride (0x0205D5DC passes 0x3D to the
`mla` at 0x02066C70). Trace what it indexes before making descriptions longer.

### 2.3 Menu, battle, shop, and item words (the program's own tables)

Short words (item names, battle messages, shop lines, menu labels) are tables inside the game's program, packed
one after another, so none of them can grow where it is.

| Table | Entries | Text bytes | References to repoint |
| --- | --- | --- | --- |
| Misc (0x020A3CDC) | 40 | 320 | 5 |
| Battle messages (0x020A41DC) | 132 | 857 | 7 to 8 |
| Shop (0x020A4D28) | 130 | 1,093 | 10 |
| Item names (0x020A78EC) | 418 | 4,619 | 12 |
| Menu short strings (0x020A6438) | | | 15 |

They are small: a copy of all of them at twice the length fits easily in the new block. Moving one means copying
its offsets and text there together and changing the places in the program that hold either address (the
counts above are the literal words found; every user should be traced before a move), plus our own code's
references.

## 3. Recommendation

Build option A: the third autoload at 0x02340600 (kept below 0x02370000), the boot-time cache flush and
arena fence, two caves in patching.py and
linker.py, and the installer change; move party chat there; build and check party chat with the full release in
both editions, in the emulator, then once on the 3DS. Text needs nothing now. Before the full Retold rewrite: make the text tool
rebuild each script's text instead of appending, and measure the largest boss fights; the string tables move
when their words grow.
