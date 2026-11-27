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
--   fill ADDR LEN BYTE           fill main RAM ADDR..ADDR+LEN with BYTE
--   changed ADDR LEN BYTE LABEL  log the ranges of ADDR..ADDR+LEN that no longer hold BYTE
--   heap LABEL                   log OS heap 0: free bytes, largest free block, used bytes
--   heapwatch / heapmin LABEL    track heap 0's lowest free and smallest largest block every frame;
--                                heapmin logs them and starts over
--   speed PERCENT                emulation speed (default 800)
--   include NAME                 run emu/plans/NAME.plan (same folder as the plan) inline
--   execpoke ADDR KIND TARGET VALUE   whenever the CPU executes ADDR, write VALUE to TARGET first
--                                (a breakpoint-style poke; used to force a battle formation)
--   execpokereg ADDR REG OFFSET KIND VALUE   whenever the CPU executes ADDR, write VALUE to [rREG] + OFFSET
--                                (e.g. a field of the battler a function was called with)
--   rec NAME EVERY TURNS SHOTTURNS [ROW]   log every frame of the next TURNS enemy turns (battle work actor
--                                >= 4 in battle main state 8) to NAME.rec, with a shot of both screens
--                                every EVERY frames during the first SHOTTURNS of them (rec/NAME_tT_fF.png); with ROW, only
--                                turns of enemies of that enemy row count
--   pinptr KIND PTR OFFSET VALUE  like pin, at [PTR] + OFFSET (the pointer is read every frame; skipped
--                                while it is null), e.g. the party's battle HP behind 0x020B8620
--   waituntil KIND ADDR VALUE N  advance frames until ADDR holds VALUE, at most N frames
--   waitrec N                    advance frames until rec has logged its turns, at most N frames
local ROOT = (os.getenv("DSDE_EMU_OUT") or "C:/Users/Jeff/Documents/Projects/Dragon Song Definitive Edition/build/emu"):gsub("\\", "/") .. "/"
local BUS = "ARM9 System Bus"

local plan_path = io.open(ROOT .. "plan_path.txt"):read("*l")
local log = io.open(ROOT .. "run.log", "w")
local frame = 0
local watches = {}
local pins = {}
local held = {}
local rec = nil -- enemy turn recorder (see `rec`)
local execpoke_count = 0

local function say(msg)
	log:write(string.format("[%6d] %s\n", frame, msg))
	log:flush()
end

local function valid_ptr(p)
	return p >= 0x02000000 and p < 0x02400000
end

-- One frame of the enemy turn recorder. A turn is the run of frames in which the battle work's
-- actor (+0x32) is an enemy (>= 4) while the battle main state (0x020B0010) is 8 (the round). With a
-- row filter, turns of enemies of other rows are skipped (not logged, not counted).
function rec_frame()
	local main = memory.read_u32_le(0x020B0010, BUS)
	local work = memory.read_u32_le(0x020B8550, BUS)
	local bat = memory.read_u32_le(0x020B8640, BUS)
	if not (valid_ptr(work) and valid_ptr(bat)) then
		return
	end
	local actor = memory.read_s16_le(work + 0x32, BUS)
	local active = main == 8 and actor >= 4 and actor < 12
	local current = active and actor or -1
	if current ~= rec.actor then
		-- the turn changed: close the open one, then maybe open a new one
		if rec.in_turn then
			rec.in_turn = false
			rec.file:write(string.format("end %d frame %d\n", rec.turn, frame))
			if rec.turn >= rec.turns then
				rec.done = true
			end
		end
		rec.actor = current
		if active and not rec.done then
			local row = memory.read_u32_le(bat + actor * 300 + 4, BUS)
			if rec.row == nil or rec.row == row then
				rec.turn = rec.turn + 1
				rec.in_turn = true
				rec.start = frame
				rec.file:write(string.format("turn %d actor %d row %d frame %d\n", rec.turn, actor, row, frame))
			end
		end
	end
	if rec.in_turn then
		local b = bat + 12 * 300
		local rs = memory.read_u16_le(work + 0x2E, BUS)
		rec.file:write(string.format("f %d rs %d step %d cnt %d scr %08X x %08X y %08X z %08X lvl %d cam %d\n",
			frame - rec.start, rs, memory.read_s16_le(b + 0xCC, BUS), memory.read_s16_le(b + 0xCE, BUS),
			memory.read_u32_le(b + 0xC8, BUS), memory.read_u32_le(b + 0xD4, BUS), memory.read_u32_le(b + 0xD8, BUS),
			memory.read_u32_le(b + 0xDC, BUS), memory.read_u32_le(0x020B8540, BUS),
			memory.read_s16_le(work + 0x36, BUS)))
		if rec.turn <= rec.shotturns and (frame - rec.start) % rec.every == 0 then
			client.screenshot(string.format("%srec/%s_t%d_f%04d.png", ROOT, rec.name, rec.turn, frame - rec.start))
		end
	end
	rec.file:flush()
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

-- OS heap 0 (the game's 2 MB main heap): the heap info sits at the main arena's start, 0x02140500
-- ({current, count, start, end, descs}); a desc is {size, free list, allocated list}, a cell {prev, next, size}.
local HEAP_INFO = 0x02140500
local heapmeter = nil -- per-frame low-water marks (see `heapwatch`)

local function heap_stats()
	local desc = memory.read_u32_le(HEAP_INFO + 0x10, BUS)
	local free_total, largest, cells = 0, 0, 0
	local cell = memory.read_u32_le(desc + 4, BUS)
	while valid_ptr(cell) and cells < 4096 do
		local size = memory.read_s32_le(cell + 8, BUS)
		free_total = free_total + size
		if size > largest then
			largest = size
		end
		cells = cells + 1
		cell = memory.read_u32_le(cell + 4, BUS)
	end
	local used, blocks = 0, 0
	cell = memory.read_u32_le(desc + 8, BUS)
	while valid_ptr(cell) and blocks < 8192 do
		used = used + memory.read_s32_le(cell + 8, BUS)
		blocks = blocks + 1
		cell = memory.read_u32_le(cell + 4, BUS)
	end
	return free_total, largest, cells, used, blocks
end

local function heap_frame()
	local free_total, largest = heap_stats()
	if free_total < heapmeter.free then
		heapmeter.free = free_total
		heapmeter.free_frame = frame
	end
	if largest < heapmeter.largest then
		heapmeter.largest = largest
		heapmeter.largest_frame = frame
	end
end

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
		if pin.ptr then
			local base = memory.read_u32_le(pin.ptr, BUS)
			if valid_ptr(base) then
				writers[pin.kind](base + pin.offset, pin.value)
			end
		else
			writers[pin.kind](pin.addr, pin.value)
		end
	end
	emu.frameadvance()
	frame = frame + 1
	if rec then
		rec_frame()
	end
	if heapmeter then
		heap_frame()
	end
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
	elseif cmd == "pinptr" then
		pins[#pins + 1] = { kind = words[2], ptr = tonumber(words[3]), offset = tonumber(words[4]), value = tonumber(words[5]) }
		say("pinptr [" .. words[3] .. "] + " .. words[4] .. " = " .. words[5])
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
	elseif cmd == "fill" then
		-- fill main RAM ADDR..ADDR+LEN with one byte value (to see later whether anything wrote there)
		local base = tonumber(words[2]) - 0x02000000
		local len = tonumber(words[3])
		local value = tonumber(words[4])
		local bytes = {}
		for i = 1, len do
			bytes[i] = value
		end
		memory.write_bytes_as_array(base, bytes, "Main RAM")
		say(string.format("fill %08X +%X = %02X", base + 0x02000000, len, value))
	elseif cmd == "changed" then
		-- log the ranges of ADDR..ADDR+LEN that no longer hold the fill byte VALUE
		local base = tonumber(words[2]) - 0x02000000
		local len = tonumber(words[3])
		local value = tonumber(words[4])
		local ram = memory.read_bytes_as_array(base, len, "Main RAM")
		local ranges = {}
		local total = 0
		local start = nil
		for i = 1, len + 1 do
			local diff = i <= len and ram[i] ~= value
			if diff then
				total = total + 1
				if start == nil then
					start = i
				end
			elseif start ~= nil then
				ranges[#ranges + 1] = string.format("%08X+%X", 0x02000000 + base + start - 1, i - start)
				start = nil
			end
		end
		local shown = {}
		for i = 1, math.min(#ranges, 40) do
			shown[i] = ranges[i]
		end
		say(string.format("changed %s %d bytes in %d ranges: %s", words[5] or "", total, #ranges, table.concat(shown, " ")))
	elseif cmd == "heap" then
		local free_total, largest, cells, used, blocks = heap_stats()
		say(string.format("heap %s free %d (largest %d, %d free cells) used %d in %d blocks", words[2] or "", free_total, largest, cells, used, blocks))
	elseif cmd == "heapwatch" then
		heapmeter = { free = math.huge, largest = math.huge, free_frame = frame, largest_frame = frame }
	elseif cmd == "heapmin" then
		say(string.format("heapmin %s lowest free %d (frame %d), smallest largest block %d (frame %d)", words[2] or "", heapmeter.free, heapmeter.free_frame, heapmeter.largest, heapmeter.largest_frame))
		heapmeter = { free = math.huge, largest = math.huge, free_frame = frame, largest_frame = frame }
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
	elseif cmd == "execpoke" then
		local target, kind, value = tonumber(words[4]), words[3], tonumber(words[5])
		execpoke_count = execpoke_count + 1
		event.on_bus_exec(function()
			writers[kind](target, value)
		end, tonumber(words[2]), "execpoke" .. execpoke_count)
		say("execpoke at " .. words[2] .. ": " .. words[4] .. " = " .. words[5])
	elseif cmd == "execpokereg" then
		local reg, offset, kind, value = "ARM9 r" .. words[3], tonumber(words[4]), words[5], tonumber(words[6])
		execpoke_count = execpoke_count + 1
		event.on_bus_exec(function()
			local base = emu.getregisters()[reg]
			if base and valid_ptr(base) then
				writers[kind](base + offset, value)
			end
		end, tonumber(words[2]), "execpoke" .. execpoke_count)
		say("execpokereg at " .. words[2] .. ": [r" .. words[3] .. "] + " .. words[4] .. " = " .. words[6])
	elseif cmd == "rec" then
		rec = { name = words[2], every = tonumber(words[3]), turns = tonumber(words[4]),
			shotturns = tonumber(words[5] or words[4]), row = tonumber(words[6] or ""), turn = 0,
			in_turn = false, done = false, actor = -1,
			file = io.open(ROOT .. words[2] .. ".rec", "w") }
		say("rec " .. words[2])
	elseif cmd == "waituntil" then
		local kind, addr, value, limit = words[2], tonumber(words[3]), tonumber(words[4]), tonumber(words[5])
		local n = 0
		while readers[kind](addr) ~= value and n < limit do
			step(nil)
			n = n + 1
		end
		if readers[kind](addr) == value then
			say(string.format("waituntil %s = %s after %d frames", words[3], words[4], n))
		else
			say(string.format("waituntil %s = %s TIMED OUT after %d frames", words[3], words[4], n))
		end
	elseif cmd == "waitrec" then
		local limit = tonumber(words[2])
		local n = 0
		while rec and not rec.done and n < limit do
			step(nil)
			n = n + 1
		end
		say(string.format("waitrec done=%s turns=%d after %d frames", tostring(rec and rec.done), rec and rec.turn or 0, n))
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
