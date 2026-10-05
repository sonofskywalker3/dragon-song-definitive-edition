-- Runs a plan file of simple commands against the game, then quits.
-- The plan path comes from build/emu/plan_path.txt (written by the Python runner).
-- Commands, one per line (# starts a comment):
--   wait N                       advance N frames
--   press BTN[,BTN...] N         hold buttons for N frames, then release for 2 frames
--   touch X Y N                  touch the bottom screen at X,Y for N frames
--   shot NAME                    screenshot to build/emu/NAME.png
--   save NAME / load NAME        savestate to/from build/emu/states/NAME.State
--   peek u8|u16|u32 ADDR LABEL   log a value from the ARM9 bus
--   poke u8|u16|u32 ADDR VALUE   write a value to the ARM9 bus
--   watch u8|u16|u32 ADDR LABEL  log the value every frame it changes from now on
--   speed PERCENT                emulation speed (default 800)
--   include NAME                 run emu/plans/NAME.plan (same folder as the plan) inline
local ROOT = "C:/Users/Jeff/Documents/Projects/Dragon Song Definitive Edition/build/emu/"
local BUS = "ARM9 System Bus"

local plan_path = io.open(ROOT .. "plan_path.txt"):read("*l")
local log = io.open(ROOT .. "run.log", "w")
local frame = 0
local watches = {}

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

local function step(input)
	if input then
		joypad.set(input)
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

local function hold(input, n)
	for _ = 1, n do
		step(input)
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
	elseif cmd == "touch" then
		hold({ Touch = true, ["Touch X"] = tonumber(words[2]), ["Touch Y"] = tonumber(words[3]) }, tonumber(words[4]))
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
	elseif cmd == "poke" then
		writers[words[2]](tonumber(words[3]), tonumber(words[4]))
		say("poke " .. words[3] .. " = " .. words[4])
	elseif cmd == "watch" then
		local w = { kind = words[2], addr = tonumber(words[3]), label = words[4] or words[3] }
		w.last = readers[w.kind](w.addr)
		say(string.format("watch %s starts at %d (0x%X)", w.label, w.last, w.last))
		watches[#watches + 1] = w
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
