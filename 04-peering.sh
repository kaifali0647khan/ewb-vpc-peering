#!/usr/bin/env bash
# Creates + accepts the peering connection and adds all 3 routes (workbook pages 9-10).
source "$(dirname "$0")/lib.sh"; need_aws
set -e
[ -z "${VPC_A:-}" ] && { echo "Run 01-deploy.sh first."; exit 1; }
[ -n "${PCX:-}" ] && { echo "Peering already created: $PCX"; exit 1; }
save PCX "$(aws ec2 create-vpc-peering-connection --vpc-id $VPC_A --peer-vpc-id $VPC_B --tag-specifications "$(ts vpc-peering-connection ewb-a-b-peer)" --query VpcPeeringConnection.VpcPeeringConnectionId --output text)"
echo "Requested $PCX - accepting..."
aws ec2 wait vpc-peering-connection-exists --vpc-peering-connection-ids $PCX
aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id $PCX >/dev/null
for i in $(seq 1 20); do
  S=$(aws ec2 describe-vpc-peering-connections --vpc-peering-connection-ids $PCX --query 'VpcPeeringConnections[0].Status.Code' --output text)
  [ "$S" = "active" ] && break; sleep 3
done
echo "Peering status: $S"; [ "$S" = "active" ] || exit 1
aws ec2 create-route --route-table-id $RT_A_PRIV --destination-cidr-block 10.20.0.0/16 --vpc-peering-connection-id $PCX >/dev/null
aws ec2 create-route --route-table-id $RT_B_PRIV --destination-cidr-block 10.10.0.0/16 --vpc-peering-connection-id $PCX >/dev/null
aws ec2 create-route --route-table-id $RT_A_PUB  --destination-cidr-block 10.20.0.0/16 --vpc-peering-connection-id $PCX >/dev/null
echo "3 routes added. Waiting 20s for routes to settle..."; sleep 20
echo "NEXT: ./05-verify.sh"
