#!/usr/bin/env bash
# Use this if bastion SSH times out because your home/mobile IP changed.
source "$(dirname "$0")/lib.sh"; need_aws
NEW=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
aws ec2 revoke-security-group-ingress --group-id $SG_BASTION --protocol tcp --port 22 --cidr "$MY_IP/32" >/dev/null 2>&1 || true
aws ec2 authorize-security-group-ingress --group-id $SG_BASTION --protocol tcp --port 22 --cidr "$NEW/32" >/dev/null
save MY_IP "$NEW"; echo "Bastion SSH rule updated to $NEW/32"
