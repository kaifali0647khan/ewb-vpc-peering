#!/usr/bin/env bash
# Writes the ProxyJump entries from workbook page 8 into ~/.ssh/config
source "$(dirname "$0")/lib.sh"
[ -z "${BASTION_IP:-}" ] && { echo "Run 01-deploy.sh first."; exit 1; }
mkdir -p ~/.ssh; touch ~/.ssh/config; cp ~/.ssh/config ~/.ssh/config.bak-ewb
sed -i.tmp '/# >>> EWB-LAB/,/# <<< EWB-LAB/d' ~/.ssh/config; rm -f ~/.ssh/config.tmp
cat >> ~/.ssh/config <<CFG
# >>> EWB-LAB
Host ewb-bastion
    HostName $BASTION_IP
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new

Host ewb-app-a
    HostName 10.10.2.10
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
    ProxyJump ewb-bastion

Host ewb-app-b
    HostName 10.20.1.10
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
    ProxyJump ewb-bastion
# <<< EWB-LAB
CFG
chmod 600 ~/.ssh/config
echo "Testing bastion..."; ssh -o ConnectTimeout=15 ewb-bastion 'echo "bastion OK: $(hostname)"' || { echo "Bastion SSH failed. If your internet IP changed, run ./fix-my-ip.sh"; exit 1; }
echo "Testing App-A through bastion..."; ssh -o ConnectTimeout=15 ewb-app-a 'echo "app-a OK: $(hostname)"' || exit 1
echo "NEXT: ./03-baseline-test.sh"
