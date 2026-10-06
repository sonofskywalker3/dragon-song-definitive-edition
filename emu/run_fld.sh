#!/bin/bash
# Runs the fld_* field test plans in order (parts 1, 2, rounds of 3 until kills == total, 4).
# Example: bash emu/run_fld.sh build/par_c/dsde_c.nds build/par_c fld_1_arrive
cd "/c/Users/Jeff/Documents/Projects/Dragon Song Definitive Edition"
ROM=$1; OUT=$2; ARR=$3
run() { uv run python -m dsde.emu emu/plans/$1.plan --rom $ROM --save --out $OUT >/dev/null 2>&1; cp $OUT/run.log $OUT/log_$2.txt; }
run $ARR 1
run fld_2_respawn 2
cp $OUT/states/fld_back.State $OUT/states/fld_round.State
for r in 1 2 3 4 5 6 7; do
  run fld_3_round r$r
  k=$(grep "peek kills_round" $OUT/log_r$r.txt | sed 's/.*= \([0-9]*\) .*/\1/'); t=$(grep "peek total_round" $OUT/log_r$r.txt | sed 's/.*= \([0-9]*\) .*/\1/')
  echo "round $r kills $k total $t" >> $OUT/rounds.txt
  [ "$k" = "$t" ] && break
done
run fld_4_after_clear 4
echo done >> $OUT/rounds.txt
