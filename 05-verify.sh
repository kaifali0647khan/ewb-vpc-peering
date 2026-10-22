#!/usr/bin/env bash
# Runs tests 02-05 and the controlled failure (workbook page 11). Saves real output to evidence/.
source "$(dirname "$0")/lib.sh"; need_aws
[ -z "${PCX:-}" ] && { echo "Run 04-peering.sh first."; exit 1; }
S="ssh -o ConnectTimeout=15"

{ stamp "TEST 02 / Forward path - inside App-A: ping App-B"
  echo '$ ssh ewb-app-a'; echo '[ec2-user@app-a ~]$ hostname; hostname -I; ping -c 4 10.20.1.10'
  $S ewb-app-a 'hostname; hostname -I; ping -c 4 10.20.1.10' 2>&1
} | tee evidence/21-test02-forward.txt

{ stamp "TEST 03 / Reverse path - inside App-B: ping App-A"
  echo '$ ssh ewb-app-b'; echo '[ec2-user@app-b ~]$ hostname; hostname -I; ping -c 4 10.10.2.10'
  $S ewb-app-b 'hostname; hostname -I; ping -c 4 10.10.2.10' 2>&1
} | tee evidence/22-test03-reverse.txt

{ stamp "TEST 04 / Private SSH - laptop to App-B through the bastion (ProxyJump)"
  echo '$ ssh ewb-app-b'
  $S ewb-app-b 'echo "Connected to: $(hostname)  private IP: $(hostname -I)"; echo "Peer path works: bastion -> peering -> App-B"' 2>&1
} | tee evidence/23-test04-ssh-appb.txt

{ stamp "TEST 05 / Isolation - public IPv4 of App-A and App-B (expected: None)"
  for pair in "ewb-app-a:$I_APP_A" "ewb-app-b:$I_APP_B"; do
    n=${pair%%:*}; i=${pair##*:}
    echo "$n ($i)  PublicIpAddress = $(aws ec2 describe-instances --instance-ids $i --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"
  done
  echo "ewb-bastion ($I_BASTION)  PublicIpAddress = $BASTION_IP   (public by design)"
} | tee evidence/24-test05-isolation.txt

echo; echo "==> Controlled failure: removing ONLY the ICMP rule on ewb-sg-app-b"
RULE="IpProtocol=icmp,FromPort=8,ToPort=0,IpRanges=[{CidrIp=10.10.2.10/32}]"
{ stamp "CONTROLLED FAILURE - remove App-B ICMP Echo rule, test, restore, test"
  echo "[1] Removing ICMP rule (10.10.2.10/32) from ewb-sg-app-b ($SG_APP_B). SSH rule stays."
  aws ec2 revoke-security-group-ingress --group-id $SG_APP_B --ip-permissions "$RULE" >/dev/null && echo "    rule removed"
  sleep 8
  echo; echo "[2] From App-A: ping -c 4 -W 2 10.20.1.10   (expected: FAIL)"
  $S ewb-app-a 'ping -c 4 -W 2 10.20.1.10' 2>&1 || true
  echo; echo "[3] Restoring the exact ICMP rule"
  aws ec2 authorize-security-group-ingress --group-id $SG_APP_B --ip-permissions "IpProtocol=icmp,FromPort=8,ToPort=0,IpRanges=[{CidrIp=10.10.2.10/32,Description=Echo-request}]" >/dev/null && echo "    rule restored"
  sleep 8
  echo; echo "[4] From App-A: ping -c 4 10.20.1.10   (expected: SUCCESS)"
  $S ewb-app-a 'ping -c 4 10.20.1.10' 2>&1
  echo; echo "Explanation: peering and routes were untouched; only the destination security group stopped allowing ICMP, so packets were dropped at App-B."
} | tee evidence/25-controlled-failure.txt
echo; echo "NEXT: ./06-inventory.sh"
