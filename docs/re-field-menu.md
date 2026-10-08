# Field menu, Start guidebook and Select (research 2026-10-08)

## Modes and keys

- Main loop: mode function table at 0x020A062C: 1 field `func_0201e6a0`, 2 town menu, 3 battle, 5 field menu
  `func_02059f84`, 6 quit to title. Current mode 0x020B000C; the mode's state 0x020B0010.
- Pad struct 0x020AFF74: +6 new presses, +8 released, +0xA held, +0xC last frame. X (0x400) and Y (0x800) come from
  ARM7 0x027FFFA8 << 10. No key repeat in the pad itself.
- Field walking is state 0x14 (0x0201F088), new keys in r7: X or the touch Menu button -> state 0xA6 (30-frame
  fade at 0x02021468) -> 0xA7 -> mode 5. R toggles walk/run. Y -> state 0x20, script 018 (think-aloud). Start ->
  state 0xCC (30-frame fade) -> 0xCE runs script 027 (the guidebook). Nothing read Select (4).

## Menu (mode 5)

- Top menu cursor byte 0x02139F40 (entries 0 Status, 2 Magic, 4 Items, 6 grey-box entry (unidentified), 8 System);
  0x02139F44 is the key mode (0 on a screen's first frame, cursor forced to 0). System list: 0 Message Speed
  (state 0x38), 2 Save (0x3B -> slot screen 0x3D), 4 Music Hall, 6 Quit Game (0x43).
- B returns 5 from `func_02058b64` and means back on every screen. Screens allocate heap buffers
  (`func_02066c88`, kept at 0x02139EF0/EEC/F2C) that only their own back paths free, so an exit must go back
  through them: jumping to the exit states 0x5C/0x5D would leak or corrupt the heap.
- Every screen change goes through state 0x4F (0x02061C64), going back through 0x5B: each waited for the icon
  press and tab animations (about 20 frames) and a 19-frame floor. Opening the menu took 72 frames from X to the
  first input, Status 42, back 41, closing 90 (19 + fade 30 + field reload about 41). Key repeat
  (`func_020591a4`): 29 frames, then every frame.

`field-menu` (feat_field_menu.py), measured (`test_field_menu`, `test_field_menu_save`):
- Select in the field opens the save screen: behind a black screen it presses A on System and on Save with
  screen changes instant (Jeff, 2026-10-08: skip the picking, do not show it), the save screen in 47 frames;
  A, A saves ("Save complete"); B goes back to the System list.
- Select in the menu presses B every frame, behind a black screen and with screen changes instant, until the
  menu exits; the screen stays black until the field fades in. The field clears the flags every frame. On the
  "saved" message (state 0x42, A only) and the 240-frame message (0x50) it waits for them to end.
- Screen waits 19 -> 6 frames and no animation wait; fades 30 -> 10; key repeat 12, then every 4. First input
  after X 37 frames (was 72), Status 11 (42), back about 10 (41). Not checked: Magic, the grey-box entry,
  Message Speed, Music Hall. The menu load (about 22) and field reload (about 41) remain.

## Start: the Adventure Guidebook (`guidebook`, 2026-10-08)

Script 027 (`build/unpacked/script/027.bin`) shows one page and closes on A, B or touch. Op 0x32 sub 0x31 tests the
map id (0x020B6BE4) < 0x97: towns (0x97 and up) show the Towns page, lower maps the Fields page. The pages are
pictures in pack.dat (archive 0): Towns 0xAA palette, 0xAB top, 0xAC bottom; Fields 0xAD, 0xAE, 0xAF (0xB0..0xB2
is Game Over). Each screen is a 256x192 8bpp bitmap (49152 bytes unpacked); both screens share one 256-colour
palette. Rendered copies from research: build/diag_menu_guide/.

Current text (line breaks at the ruled lines, original spelling):
- Towns. Run: "Hold the B Button when moving to run. Running consumes HP, and at 1/3 HP you can no longer run."
  Heal: "Althena Statues can be seen in many places. Press the A Button in front of one to fully heal." Save: "Save
  the game to continue play later. Select [hammer] from the menu screen, and then save. You can save up to 3
  games." Equip: "Select [bag] from the menu screen and select the item to change. Use A Button or touch to
  select. and L Button or R Button to Change members."
- Fields. Combat Mode: "Defeat monsters to get items. Althena Conducts cannot be earned. Use AC to power up
  characters. Monsters will revive later." Virtue Mode: "Defeat monsters and get Althena Conducts, but not items.
  A check will be awarded per win. Monsters won' t revive here." Clock&Check: "After each win the clock fills to
  MAX, then gradually decreases. After each revolution, a check is gone and a monster will revive." Blue Boxes:
  "Clear map of all monsters in Virtue mode and all check boxes are checked, then the blue boxes will open, and
  30% HP and MP will be regained."

Out of date: Run (no HP cost, timed run) and the whole Fields page (one battle mode, no clock, no clear refill,
restock on entry, Experience). Heal, Save and Equip still hold. Plan: redraw the ruled-line text into the vanilla
bitmaps at build time (DataPatch of pack entries 0xAB/0xAC/0xAE/0xAF), keeping the panels and using existing
palette indexes; glyphs cut from the vanilla bitmaps or the dialogue font. The Blue Boxes panel becomes
"Blue Chest" (Jeff: singular). Draft panel texts are in the session notes of 2026-10-08 (playtest-feedback item 20.1).

Built (feat_guidebook.py, guidebook_font.py, guidebook_pages.py): the body letters are cut from the vanilla lines
whose pieces match their characters one to one (lines sit at whole-row offsets, found from their ink profiles);
E, F, H, N, O, T, j, 3, comma, parentheses, and + are drawn by hand in the same style. Changed lines are wiped
to the paper colour of each row and the new text wrapped over the same ruled lines (letter gap 1, word gap 6,
text no further right than column 117, as vanilla). Headings are white letters with a 2-pixel black outline, as
vanilla (the outlines merge into the pill look). Changed: Towns Run (all), Save (from "save." on); Fields all four
panels and headings (Battles, Speed, Enemies, Blue Chest). `test_guidebook`: both pages in game.
