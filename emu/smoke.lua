-- Boot test: run the game for a while, take screenshots, report state, then quit.
local OUT = "C:/Users/Jeff/Documents/Projects/Dragon Song Definitive Edition/build/emu/"
local log = io.open(OUT .. "smoke.log", "w")

local function say(msg)
	log:write(msg .. "\n")
	log:flush()
end

say("system " .. emu.getsystemid())
local buttons = joypad.get()
local names = {}
for k, _ in pairs(buttons) do
	names[#names + 1] = k
end
table.sort(names)
say("buttons " .. table.concat(names, ","))

client.speedmode(800)
for frame = 1, 1800 do
	emu.frameadvance()
	if frame % 600 == 0 then
		client.screenshot(OUT .. "smoke_" .. frame .. ".png")
		say("frame " .. frame)
	end
end
say("done")
log:close()
client.exit()
