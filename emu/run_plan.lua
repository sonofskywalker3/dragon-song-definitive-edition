-- Runs a plan file of simple commands against the game, then quits.
-- The plan path comes from <out>/plan_path.txt (written by the Python runner), where <out> is
-- $DSDE_EMU_OUT or build/emu. Separate out dirs let several emulators run at once.
-- Commands, one per line (# starts a comment):
--   wait N                       advance N frames
--   press BTN[,BTN...] N         hold buttons for N frames, then release for 2 frames
--   hold BTN[,BTN...]            keep buttons down during the following commands until release
--   release                      let go of held buttons
--   touch X Y N                  touch the bottom screen at X,Y for N frames
--   shot NAME                    screenshot to build/emu/NAME.png
--   save NAME / load NAME        savestate to/from build/emu/states/NAME.State
--   peek u8|u16|u32 ADDR LABEL   log a value from the ARM9 bus
--   dump ADDR LEN LABEL          log LEN bytes as u32 words
--   poke u8|u16|u32 ADDR VALUE   write a value to the ARM9 bus
--   watch u8|u16|u32 ADDR LABEL  log the value every frame it changes from now on
--   pin u8|u16|u32 ADDR VALUE    write a value before every frame until unpin
--   unpin                        drop all pins
--   trace ADDR LABEL             log CPU registers whenever ADDR is written
--   find HEXBYTES LABEL          log every main RAM address where the byte pattern occurs
--   speed PERCENT                emulation speed (default 800)
--   include NAME                 run emu/plans/NAME.plan (same folder as the plan) inline
local ROOT = (os.getenv("DSDE_EMU_OUT") or "C:/Users/Jeff/Documents/Projects/Dragon Song Definitive Edition/build/emu"):gsub("\\", "/") .. "/"
local BUS = "ARM9 System Bus"

local plan_path = io.open(ROOT .. "plan_path.txt"):read("*l")
local log = io.open(ROOT .. "run.log", "w")
local frame = 0
local watches = {}
local pins = {}
local held = {}

local function say(msg)
	log:write(string.format("[%6d] %s\n", frame, msg))
	log:flush()
end

local readers = {
	u8 = function(a) return memory.read_u8(a, BUS) end,
	u16 = function(a) return memory.read_u16_le(a, BUS) end,
	u32 = function(a) return memory.read_u32_le(a, BUS) end,
}
local writers = {
	u8 = function(a, v) memory.write_u8(a, v, BUS) end,
	u16 = function(a, v) memory.write_u16_le(a, v, BUS) end,
	u32 = function(a, v) memory.write_u32_le(a, v, BUS) end,
}

local function step(input, analog)
	local merged = {}
	for b, v in pairs(held) do
		merged[b] = v
	end
	for b, v in pairs(input or {}) do
		merged[b] = v
	end
	if next(merged) then
		joypad.set(merged)
	end
	if analog then
		-- touch coordinates are analog axes; joypad.set ignores them
		joypad.setanalog(analog)
	end
	for _, pin in ipairs(pins) do
		writers[pin.kind](pin.addr, pin.value)
	end
	emu.frameadvance()
	frame = frame + 1
	for _, w in ipairs(watches) do
		local v = readers[w.kind](w.addr)
		if v ~= w.last then
			say(string.format("watch %s = %d (0x%X)", w.label, v, v))
			w.last = v
		end
	end
end

local function hold(input, n, analog)
	for _ = 1, n do
		step(input, analog)
	end
end

local PLANS = plan_path:match("^(.*/)")

local function run_file(path)
for line in io.lines(path) do
	line = line:gsub("#.*", "")
	local words = {}
	for w in line:gmatch("%S+") do
		words[#words + 1] = w
	end
	local cmd = words[1]
	if cmd == "wait" then
		hold(nil, tonumber(words[2]))
	elseif cmd == "press" then
		local input = {}
		for b in words[2]:gmatch("[^,]+") do
			input[b] = true
		end
		hold(input, tonumber(words[3]))
		hold(nil, 2)
	elseif cmd == "hold" then
		for b in words[2]:gmatch("[^,]+") do
			held[b] = true
		end
		say("hold " .. words[2])
	elseif cmd == "release" then
		held = {}
		say("release")
	elseif cmd == "touch" then
		local xy = { ["Touch X"] = tonumber(words[2]), ["Touch Y"] = tonumber(words[3]) }
		hold({ Touch = true }, tonumber(words[4]), xy)
		hold(nil, 2)
	elseif cmd == "shot" then
		client.screenshot(ROOT .. words[2] .. ".png")
		say("shot " .. words[2])
	elseif cmd == "save" then
		savestate.save(ROOT .. "states/" .. words[2] .. ".State")
		say("saved " .. words[2])
	elseif cmd == "load" then
		savestate.load(ROOT .. "states/" .. words[2] .. ".State")
		say("loaded " .. words[2])
	elseif cmd == "peek" then
		local v = readers[words[2]](tonumber(words[3]))
		say(string.format("peek %s = %d (0x%X)", words[4] or words[3], v, v))
	elseif cmd == "dump" then
		local addr, len = tonumber(words[2]), tonumber(words[3])
		local parts = {}
		for i = 0, len - 1, 4 do
			parts[#parts + 1] = string.format("%08X", memory.read_u32_le(addr + i, BUS))
		end
		say(string.format("dump %s %08X: %s", words[4] or "", addr, table.concat(parts, " ")))
	elseif cmd == "poke" then
		writers[words[2]](tonumber(words[3]), tonumber(words[4]))
		say("poke " .. words[3] .. " = " .. words[4])
	elseif cmd == "watch" then
		local w = { kind = words[2], addr = tonumber(words[3]), label = words[4] or words[3] }
		w.last = readers[w.kind](w.addr)
		say(string.format("watch %s starts at %d (0x%X)", w.label, w.last, w.last))
		watches[#watches + 1] = w
	elseif cmd == "pin" then
		pins[#pins + 1] = { kind = words[2], addr = tonumber(words[3]), value = tonumber(words[4]) }
		say("pin " .. words[3] .. " = " .. words[4])
	elseif cmd == "unpin" then
		pins = {}
		say("unpin all")
	elseif cmd == "find" then
		local pat = {}
		for byte in words[2]:gmatch("%x%x") do
			pat[#pat + 1] = tonumber(byte, 16)
		end
		local ram = memory.read_bytes_as_array(0, 0x400000, "Main RAM")
		local hits = {}
		for i = 1, #ram - #pat + 1 do
			local ok = true
			for j = 1, #pat do
				if ram[i + j - 1] ~= pat[j] then
					ok = false
					break
				end
			end
			if ok then
				hits[#hits + 1] = string.format("%08X", 0x02000000 + i - 1)
			end
		end
		say("find " .. (words[3] or words[2]) .. " " .. table.concat(hits, " "))
	elseif cmd == "trace" then
		-- log CPU registers on every write to ADDR
		local label = words[3] or words[2]
		event.on_bus_write(function(addr)
			local r = emu.getregisters()
			local parts = {}
			for _, k in ipairs({ "ARM9 r15", "ARM9 r14", "ARM9 r0", "ARM9 r1", "ARM9 r2" }) do
				parts[#parts + 1] = string.format("%s=%08X", k, r[k] or 0)
			end
			say("trace " .. label .. " " .. table.concat(parts, " "))
		end, tonumber(words[2]), label)
		say("trace on " .. words[2])
	elseif cmd == "exec" then
		-- log registers whenever the CPU executes ADDR
		local label = words[3] or words[2]
		event.on_bus_exec(function()
			local r = emu.getregisters()
			local parts = {}
			for _, k in ipairs({ "ARM9 r0", "ARM9 r1", "ARM9 r2", "ARM9 r3", "ARM9 r4", "ARM9 r5", "ARM9 r6", "ARM9 r7", "ARM9 r14" }) do
				parts[#parts + 1] = string.format("%s=%08X", k:sub(6), r[k] or 0)
			end
			say("exec " .. label .. " " .. table.concat(parts, " "))
		end, tonumber(words[2]), label)
		say("exec on " .. words[2])
	elseif cmd == "battlers" then
		-- battler objects: 300 bytes each from the pointer at 0x020B8640
		local base = memory.read_u32_le(0x020B8640, BUS)
		local parts = {}
		for i = 0, 13 do
			local o = base + i * 300
			parts[#parts + 1] = string.format("%d:f%08X/c%d/r%d", i, memory.read_u32_le(o, BUS),
				memory.read_u32_le(o + 4, BUS), memory.read_u32_le(o + 0x10, BUS))
		end
		say("battlers " .. table.concat(parts, " "))
	elseif cmd == "speed" then
		client.speedmode(tonumber(words[2]))
	elseif cmd == "include" then
		run_file(PLANS .. words[2] .. ".plan")
	elseif cmd ~= nil then
		say("unknown command " .. cmd)
	end
end
end

client.speedmode(800)
run_file(plan_path)
say("plan done")
log:close()
client.exit()
