#!/usr/bin/env bash
# TEST 01: before peering, App-A cannot reach App-B. Expected: 100% packet loss.
source "$(dirname "$0")/lib.sh"
[ -n "${PCX:-}" ] && { echo "Peering already exists - baseline must be captured BEFORE peering."; exit 1; }
OUT=evidence/20-test01-baseline.txt
{ stamp "TEST 01 / Baseline (before peering) - run inside App-A"
  echo '$ ssh ewb-app-a'; echo '[ec2-user@app-a ~]$ hostname; hostname -I; ping -c 4 -W 2 10.20.1.10'
  ssh -o ConnectTimeout=15 ewb-app-a 'hostname; hostname -I; ping -c 4 -W 2 10.20.1.10' 2>&1 || true
} | tee $OUT
echo; echo "Saved $OUT  (expected: 100% packet loss)"; echo "NEXT: ./04-peering.sh"
