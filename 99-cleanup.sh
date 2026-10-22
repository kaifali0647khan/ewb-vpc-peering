#!/usr/bin/env bash
# Deletes EVERYTHING created by this kit, in the right order, then verifies nothing is left.
source "$(dirname "$0")/lib.sh"; need_aws
echo "This DELETES all lab resources. Have you taken your console screenshots and run 06-inventory.sh + make_report.py?"
read -r -p "Type DELETE to continue: " a; [ "$a" = "DELETE" ] || exit 0
q() { "$@" >/dev/null 2>&1 || true; }
OUT=evidence/30-cleanup.txt
{ stamp "Cleanup log"
echo "[1] Terminating instances"; q aws ec2 terminate-instances --instance-ids $I_BASTION $I_APP_A $I_APP_B
aws ec2 wait instance-terminated --instance-ids $I_BASTION $I_APP_A $I_APP_B && echo "    all 3 terminated"
echo "[2] Deleting peer routes and peering"
q aws ec2 delete-route --route-table-id $RT_A_PRIV --destination-cidr-block 10.20.0.0/16
q aws ec2 delete-route --route-table-id $RT_B_PRIV --destination-cidr-block 10.10.0.0/16
q aws ec2 delete-route --route-table-id $RT_A_PUB  --destination-cidr-block 10.20.0.0/16
q aws ec2 delete-vpc-peering-connection --vpc-peering-connection-id $PCX; sleep 5
echo "[3] Deleting security groups"; sleep 15
for sg in $SG_BASTION $SG_APP_A $SG_APP_B; do for i in 1 2 3 4; do aws ec2 delete-security-group --group-id $sg >/dev/null 2>&1 && break; sleep 10; done; done
echo "[4] Subnet associations, subnets, route tables"
q aws ec2 disassociate-route-table --association-id $ASSOC_A_PUB
q aws ec2 disassociate-route-table --association-id $ASSOC_A_PRIV
q aws ec2 disassociate-route-table --association-id $ASSOC_B_PRIV
for s in $SUBNET_A_PUB $SUBNET_A_PRIV $SUBNET_B_PRIV; do q aws ec2 delete-subnet --subnet-id $s; done
for r in $RT_A_PUB $RT_A_PRIV $RT_B_PRIV; do q aws ec2 delete-route-table --route-table-id $r; done
echo "[5] Internet gateway"; q aws ec2 detach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC_A; q aws ec2 delete-internet-gateway --internet-gateway-id $IGW
echo "[6] VPCs"; q aws ec2 delete-vpc --vpc-id $VPC_A; q aws ec2 delete-vpc --vpc-id $VPC_B
echo "[7] Key pair (AWS side) and local .pem"; q aws ec2 delete-key-pair --key-name ewb-lab; rm -f ~/.ssh/ewb-lab.pem
sed -i.tmp '/# >>> EWB-LAB/,/# <<< EWB-LAB/d' ~/.ssh/config 2>/dev/null; rm -f ~/.ssh/config.tmp
echo; echo "=== VERIFY: resources still tagged Project=EWB-VPC-Peering (all lists should be empty) ==="
F="Name=tag:Project,Values=EWB-VPC-Peering"
echo "VPCs:        $(aws ec2 describe-vpcs --filters $F --query 'Vpcs[].VpcId' --output text)"
echo "Subnets:     $(aws ec2 describe-subnets --filters $F --query 'Subnets[].SubnetId' --output text)"
echo "Instances:   $(aws ec2 describe-instances --filters $F Name=instance-state-name,Values=pending,running,stopped,stopping --query 'Reservations[].Instances[].InstanceId' --output text)"
echo "Volumes:     $(aws ec2 describe-volumes --filters $F --query 'Volumes[].VolumeId' --output text)"
echo "Peerings:    $(aws ec2 describe-vpc-peering-connections --filters Name=status-code,Values=active,pending-acceptance --query 'VpcPeeringConnections[?Tags[?Key==`Project`&&Value==`EWB-VPC-Peering`]].VpcPeeringConnectionId' --output text)"
echo "Elastic IPs: $(aws ec2 describe-addresses --query 'Addresses[].PublicIp' --output text)"
echo "Key pairs:   $(aws ec2 describe-key-pairs --query 'KeyPairs[?KeyName==`ewb-lab`].KeyName' --output text)"
echo "(blank after a label = nothing left)"
} 2>&1 | tee $OUT
mv ids.env ids.env.cleaned-$(date +%s) 2>/dev/null; touch ids.env
echo; echo "Cleanup done. Re-run: python3 make_report.py  (it will now include the cleanup evidence)"
