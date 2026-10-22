#!/usr/bin/env bash
# Captures VPC/subnet/route-table/SG/instance/peering inventory as evidence.
source "$(dirname "$0")/lib.sh"; need_aws
F="Name=tag:Project,Values=EWB-VPC-Peering"
NAME='Tags[?Key==`Name`]|[0].Value'
{ stamp "Inventory: VPCs and subnets"
  aws ec2 describe-vpcs --filters $F --query "Vpcs[].{Name:$NAME,VpcId:VpcId,CIDR:CidrBlock,State:State}" --output table
  aws ec2 describe-subnets --filters $F --query "Subnets[].{Name:$NAME,SubnetId:SubnetId,VpcId:VpcId,CIDR:CidrBlock,AZ:AvailabilityZone,AutoPublicIP:MapPublicIpOnLaunch}" --output table
  aws ec2 describe-internet-gateways --filters $F --query "InternetGateways[].{Name:$NAME,IGW:InternetGatewayId,AttachedTo:Attachments[0].VpcId}" --output table
} > evidence/10-inventory-vpcs-subnets.txt
{ stamp "Route tables, subnet associations and routes"
  for rt in $RT_A_PUB $RT_A_PRIV $RT_B_PRIV; do
    echo "=== $(aws ec2 describe-route-tables --route-table-ids $rt --query "RouteTables[0].$NAME" --output text)  ($rt)"
    echo "Associated subnet: $(aws ec2 describe-route-tables --route-table-ids $rt --query 'RouteTables[0].Associations[?SubnetId!=`null`].SubnetId' --output text)"
    aws ec2 describe-route-tables --route-table-ids $rt --query 'RouteTables[0].Routes[].{Destination:DestinationCidrBlock,Target:GatewayId||VpcPeeringConnectionId,State:State}' --output table
  done
} > evidence/11-route-tables.txt
{ stamp "Security group inbound rules"
  for sg in $SG_BASTION $SG_APP_A $SG_APP_B; do
    echo "=== $(aws ec2 describe-security-groups --group-ids $sg --query 'SecurityGroups[0].GroupName' --output text)  ($sg)"
    aws ec2 describe-security-groups --group-ids $sg --query 'SecurityGroups[0].IpPermissions[].{Protocol:IpProtocol,From:FromPort,To:ToPort,Source:IpRanges[0].CidrIp}' --output table
  done
} > evidence/12-security-groups.txt
{ stamp "Instances"
  aws ec2 describe-instances --filters $F Name=instance-state-name,Values=running --query "Reservations[].Instances[].{Name:$NAME,InstanceId:InstanceId,PrivateIP:PrivateIpAddress,PublicIP:PublicIpAddress,Subnet:SubnetId,Type:InstanceType}" --output table
} > evidence/13-instances.txt
{ stamp "Peering connection"
  aws ec2 describe-vpc-peering-connections --vpc-peering-connection-ids $PCX --query "VpcPeeringConnections[].{Name:$NAME,PeeringId:VpcPeeringConnectionId,Status:Status.Code,Requester:RequesterVpcInfo.VpcId,RequesterCIDR:RequesterVpcInfo.CidrBlock,Accepter:AccepterVpcInfo.VpcId,AccepterCIDR:AccepterVpcInfo.CidrBlock}" --output table
} > evidence/14-peering.txt
cat evidence/1[0-4]-*.txt
echo; echo "Saved to evidence/. NEXT: take the console screenshots (see README), then: python3 make_report.py"
