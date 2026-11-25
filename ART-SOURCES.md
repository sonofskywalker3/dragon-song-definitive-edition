# Art sources

Every piece of artwork this hack adds or changes, and how it was made. I'm not an artist, so some of it was
made with AI. If you would like to draw a replacement for anything here, I would love to use real art and will
credit you in full (see the end of this file).

Art copied from your own copy of the game at build time is not listed unless the build changes it.

## Battle Special list icons

Each skill in the battle Special list shows a 16 x 16 icon. The files are in [art/icons/](art/icons/); the
build reads them and converts each color to the nearest color of the game's item icon palette, so a
replacement only needs to be a 16 x 16 PNG with the same file name. The game's item icons that some of them
start from are not in this repository; the item is named so you can find it in the game.

Drawn as pixel art by a script written with AI (Claude, by Anthropic):

| File | Skill | What it shows |
|---|---|---|
| [healing_water.png](art/icons/healing_water.png) | Healing Water | a blue raindrop |
| [cure_water.png](art/icons/cure_water.png) | Cure Water | a green raindrop |
| [tender_rain.png](art/icons/tender_rain.png) | Tender Rain | a wide white cloud with rain |
| [divine_rain.png](art/icons/divine_rain.png) | Divine Rain | a gold cloud with white rain |
| [miracle_tears.png](art/icons/miracle_tears.png) | Miracle Tears | a slim purple teardrop |
| [gale_cut.png](art/icons/gale_cut.png) | Gale Cut | a gust of wind curling into a swirl |
| [blinding_gale.png](art/icons/blinding_gale.png) | Blinding Gale | the same wind with a dark purple and black glow |
| [focus.png](art/icons/focus.png) | Focus | a black crosshair |
| [knockout_kick.png](art/icons/knockout_kick.png) | Knockout Kick | a sheep |
| [venom_claw.png](art/icons/venom_claw.png) | Venom Claw | green poison bubbles |
| [venom_rain.png](art/icons/venom_rain.png) | Venom Rain | smaller, spread-out poison bubbles |
| [howl.png](art/icons/howl.png) | Howl | three black concentric circles |
| [dread_roar.png](art/icons/dread_roar.png) | Dread Roar | four black concentric circles |
| [water_bind.png](art/icons/water_bind.png) | Water Bind | three stacked blue rings |
| [binding_rain.png](art/icons/binding_rain.png) | Binding Rain | three stacks of three blue rings |
| [double_strike.png](art/icons/double_strike.png) | Double Strike | two comic-book impact bursts |
| [feral_rage.png](art/icons/feral_rage.png) | Feral Rage | three claw slashes with a green up arrow |
| [war_council.png](art/icons/war_council.png) | War Council | a folded map with a green up arrow |

Edited by the same script from one of the game's own item icons (the red and green arrows and the lightning
were drawn with AI):

| File | Skill | Game icon it starts from | Change |
|---|---|---|---|
| [weapon_break.png](art/icons/weapon_break.png) | Weapon Break | Katana | red down arrow added |
| [war_breaker.png](art/icons/war_breaker.png) | War Breaker | Crystal Sword | red down arrow added |
| [armor_break.png](art/icons/armor_break.png) | Armor Break | Silver Vest | red down arrow added |
| [wall_breaker.png](art/icons/wall_breaker.png) | Wall Breaker | Dark Vest | red down arrow added |
| [rally.png](art/icons/rally.png) | Rally | Katana | green up arrow added |
| [battle_cry.png](art/icons/battle_cry.png) | Battle Cry | Crystal Sword | green up arrow added |
| [stand_fast.png](art/icons/stand_fast.png) | Stand Fast | Silver Vest | green up arrow added |
| [shield_wall.png](art/icons/shield_wall.png) | Shield Wall | Dark Vest | green up arrow added |
| [quick_march.png](art/icons/quick_march.png) | Quick March | Boots | green up arrow added |
| [forced_march.png](art/icons/forced_march.png) | Forced March | Boots | green up arrow added |
| [stratagem.png](art/icons/stratagem.png) | Stratagem | Old Book | green up arrow added |
| [thunder_sword.png](art/icons/thunder_sword.png) | Thunder Sword | Replica Sword | two lightning bolts added along the blade |
| [blinding_swipe.png](art/icons/blinding_swipe.png) | Blinding Swipe | Glasses | lenses recolored black |

Taken from the game:

| File | Skill | Source |
|---|---|---|
| [stone_throw.png](art/icons/stone_throw.png) | Stone Throw | the stone Jian tosses in his unused throw animation, cropped and centered, unchanged |
| (no file) | Escape, Inferno, Crashing Wave, Wind Cutter, Lunar Quake | the game's Boots and the four Dragon Ring item icons, unchanged |
| (no file) | Quick, Grand Weapon, Grand Shell | the game's own spell sigil, colors moved by script to the nearest item icon palette colors |
| (no file) | a worn monster card | that card's own item icon, unchanged |

## Other changed art

These are made by the build scripts from the game's own art or drawn in code. Their sources are being
confirmed; this section will say how each was made.

| What you see | Where it is made | How |
|---|---|---|
| The red "Definitive Edition / Classic" seal on the title screen; the title art's palette merges close colors to make room | `src/dsde/feat_title_seal.py` | drawn in code; source unknown |
| The blue "Retold" seal (Retold edition) | `src/dsde/feat_title_seal.py` | the Classic seal recolored by script; source unknown |
| The battle's wooden sign reading "L+R" instead of "MIC" | `src/dsde/feat_mic_sign.py` | the game's sign with new letters drawn in code; source unknown |
| The plank under the status bar reading NORMAL, FAST, or FASTER | `src/dsde/feat_battle_speed_label.py` | letters and shading drawn in code, in the sign's style; source unknown |
| The "Bubble" icon for the Blue Dragon's summons in the target picker | `src/dsde/feat_targeting_names.py` | one frame of the bubbles' battle sprite, recolored by script to the icon palette |
| The ring slot icon on the Status page, and its greyed copy | `src/dsde/feat_card_status.py` | the game's Ring item icon, recolored by script to the menu palette |
| The flying stone of Stone Throw | `src/dsde/feat_skills_stone.py` | the stone from Jian's unused throw animation, moved into its own sprite file, unchanged |
| The redone Adventure Guidebook pages: new text, headings, and heading pills | `src/dsde/feat_guidebook.py`, `src/dsde/guidebook_font.py` | letters cut from the guidebook's own pages; a few letters (E F H N O T 3 j M) and the pills drawn in code; source unknown |
| A job's title shown in red in Gad's job list | `src/dsde/feat_gad_jobs.py` | a red copy of the title text palette, made by script |

## Contributing art

Replacements from artists are welcome and get full credit here and in the release notes. Open an issue or a
pull request, or reach out on GBAtemp. For an icon, a 16 x 16 PNG with the same file name is all it takes.
