// Creates a function (ARM or Thumb) for every function in a dsd symbols.txt, then reanalyzes.
// Usage (headless): -preScript ApplyDsdSymbols.java <path to symbols.txt>
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.ContextChangeException;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ApplyDsdSymbols extends GhidraScript {
    private static final Pattern LINE = Pattern.compile(
            "^(\\S+) kind:function\\((arm|thumb)[^)]*\\) addr:0x([0-9a-fA-F]+)");

    @Override
    public void run() throws Exception {
        Register tmode = currentProgram.getRegister("TMode");
        int created = 0;
        for (String line : Files.readAllLines(Paths.get(getScriptArgs()[0]))) {
            Matcher m = LINE.matcher(line);
            if (!m.find()) {
                continue;
            }
            Address addr = toAddr(Long.parseLong(m.group(3), 16));
            if (!currentProgram.getMemory().contains(addr)) {
                continue;
            }
            BigInteger mode = m.group(2).equals("thumb") ? BigInteger.ONE : BigInteger.ZERO;
            try {
                currentProgram.getProgramContext().setValue(tmode, addr, addr, mode);
            } catch (ContextChangeException e) {
                // Already disassembled in the other mode: clear it and retry once
                clearListing(addr);
                try {
                    currentProgram.getProgramContext().setValue(tmode, addr, addr, mode);
                } catch (ContextChangeException e2) {
                    println("skip " + addr + ": " + e2.getMessage());
                    continue;
                }
            }
            new DisassembleCommand(new AddressSet(addr), null, true).applyTo(currentProgram, monitor);
            Function fn = getFunctionAt(addr);
            if (fn == null) {
                fn = createFunction(addr, m.group(1));
            }
            if (fn != null && !m.group(1).startsWith("func_")) {
                fn.setName(m.group(1), SourceType.IMPORTED);
            }
            created++;
        }
        println("dsd functions applied: " + created);
    }
}
