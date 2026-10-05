// Decompiles every function in the program and writes them all to one C file.
// Usage (headless): -postScript DumpDecomp.java <output path>
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;

import java.io.PrintWriter;

public class DumpDecomp extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outPath = getScriptArgs()[0];
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        try (PrintWriter out = new PrintWriter(outPath, "UTF-8")) {
            for (Function fn : currentProgram.getFunctionManager().getFunctions(true)) {
                if (monitor.isCancelled()) {
                    break;
                }
                DecompileResults res = decomp.decompileFunction(fn, 60, monitor);
                out.println("// ==== " + fn.getName() + " @ " + fn.getEntryPoint());
                if (res.decompileCompleted()) {
                    out.println(res.getDecompiledFunction().getC());
                } else {
                    out.println("// decompile failed: " + res.getErrorMessage());
                }
            }
        }
        decomp.dispose();
    }
}
