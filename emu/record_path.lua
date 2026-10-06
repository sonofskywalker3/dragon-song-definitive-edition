-- Records where the player walks while a person plays (it presses nothing itself).
-- Logs to <out>/path.log, where <out> is $DSDE_EMU_OUT or build/emu: one line per map change and
-- every RECORD_EVERY frames while Jian moves, with map id, position (whole units), facing and buttons.
local ROOT = (os.getenv("DSDE_EMU_OUT") or "C:/Users/Jeff/Documents/Projects/Dragon Song Definitive Edition/build/emu"):gsub("\\", "/") .. "/"
local BUS = "ARM9 System Bus"
local MAP = 0x020B6BE4 -- s16 current map id (player block +0)
local POS_X = 0x020B6CB4 -- player block +0xD0, 20.12 fixed point
local POS_Y = 0x020B6CB8 -- player block +0xD4
local FACING = 0x020B6CC7 -- player block +0xE3, low 3 bits
local FIXED_SHIFT = 4096
local RECORD_EVERY = 4

local log = io.open(ROOT .. "path.log", "w")
local frame, last_map, last_x, last_y, last_frame = 0, -1, -1, -1, -RECORD_EVERY

local function buttons()
	local held = {}
	for name, down in pairs(joypad.get()) do
		if down == true then
			held[#held + 1] = name
		end
	end
	table.sort(held)
	return table.concat(held, ",")
end

log:write("frame map x y facing buttons\n")
while true do
	emu.frameadvance()
	frame = frame + 1
	local map = memory.read_s16_le(MAP, BUS)
	local x = memory.read_u32_le(POS_X, BUS) // FIXED_SHIFT
	local y = memory.read_u32_le(POS_Y, BUS) // FIXED_SHIFT
	local moved = x ~= last_x or y ~= last_y
	if map ~= last_map or (moved and frame - last_frame >= RECORD_EVERY) then
		local facing = memory.read_u8(FACING, BUS) % 8
		log:write(string.format("%d %d %d %d %d %s\n", frame, map, x, y, facing, buttons()))
		log:flush()
		last_map, last_x, last_y, last_frame = map, x, y, frame
	end
end
